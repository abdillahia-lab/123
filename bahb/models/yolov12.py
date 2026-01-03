"""YOLOv12 object detection model for infrastructure inspection."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from numpy.typing import NDArray
from loguru import logger

from bahb.core.config import YOLOConfig
from bahb.core.types import BoundingBox, Detection
from bahb.models.base import BaseModel


class YOLOv12Detector(BaseModel):
    """
    YOLOv12 detector optimized for infrastructure inspection.

    Features:
    - Attention-based architecture for better feature extraction
    - Multi-scale detection for varying object sizes
    - Optimized for TensorRT inference on Jetson/Orin
    """

    # Default detection classes for infrastructure
    DEFAULT_CLASSES = [
        "transformer", "insulator", "conductor", "switchgear",
        "circuit_breaker", "disconnect_switch", "capacitor_bank",
        "lightning_arrester", "server_rack", "hvac_unit",
        "cooling_fan", "electrical_panel", "cable", "ups", "pdu",
        "fire_suppression", "vegetation", "person", "vehicle",
        "damage", "corrosion", "hotspot", "leak", "crack",
        "contamination", "bird_nest"
    ]

    def __init__(self, config: YOLOConfig):
        super().__init__(
            model_path=config.weights,
            device=config.device,
            half_precision=config.half_precision,
        )
        self.config = config
        self.input_size = config.input_size
        self.conf_threshold = config.confidence_threshold
        self.nms_threshold = config.nms_threshold
        self.classes = config.classes or self.DEFAULT_CLASSES

        self._ultralytics_model = None

    def load(self) -> bool:
        """Load YOLOv12 model."""
        try:
            # Try TensorRT engine first
            engine_path = Path(self.model_path)
            if engine_path.suffix == ".engine" and engine_path.exists():
                return self._load_tensorrt()

            # Fall back to Ultralytics
            return self._load_ultralytics()

        except Exception as e:
            logger.error(f"Failed to load YOLOv12: {e}")
            return False

    def _load_tensorrt(self) -> bool:
        """Load TensorRT-optimized YOLOv12."""
        try:
            import tensorrt as trt
            import pycuda.driver as cuda
            import pycuda.autoinit  # noqa

            logger.info(f"Loading YOLOv12 TensorRT engine: {self.model_path}")

            with open(self.model_path, "rb") as f:
                runtime = trt.Runtime(trt.Logger(trt.Logger.WARNING))
                self._engine = runtime.deserialize_cuda_engine(f.read())

            if self._engine is None:
                raise RuntimeError("Failed to deserialize engine")

            self._context = self._engine.create_execution_context()
            self._stream = cuda.Stream()
            self._allocate_buffers()

            self._is_loaded = True
            logger.info("YOLOv12 TensorRT engine loaded")
            return True

        except Exception as e:
            logger.warning(f"TensorRT load failed: {e}, trying Ultralytics")
            return self._load_ultralytics()

    def _load_ultralytics(self) -> bool:
        """Load using Ultralytics library."""
        try:
            from ultralytics import YOLO

            # Try to find the model weights
            model_path = Path(self.model_path)
            if not model_path.exists():
                # Try common paths
                for ext in [".pt", ".onnx", ".engine"]:
                    alt_path = model_path.with_suffix(ext)
                    if alt_path.exists():
                        model_path = alt_path
                        break
                else:
                    # Use default YOLOv8 as fallback (YOLOv12 interface compatible)
                    logger.warning("Model not found, using yolov8l as fallback")
                    model_path = "yolov8l.pt"

            self._ultralytics_model = YOLO(str(model_path))

            # Move to device
            if "cuda" in self.device:
                self._ultralytics_model.to(self.device)

            self._is_loaded = True
            logger.info("YOLOv12 loaded via Ultralytics")
            return True

        except Exception as e:
            logger.error(f"Failed to load via Ultralytics: {e}")
            return False

    def _allocate_buffers(self) -> None:
        """Allocate TensorRT buffers."""
        import pycuda.driver as cuda
        import tensorrt as trt

        self._inputs = []
        self._outputs = []
        self._bindings = []

        for i in range(self._engine.num_io_tensors):
            name = self._engine.get_tensor_name(i)
            shape = self._engine.get_tensor_shape(name)
            dtype = trt.nptype(self._engine.get_tensor_dtype(name))

            size = int(np.prod(shape))
            host_mem = cuda.pagelocked_empty(size, dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)

            self._bindings.append(int(device_mem))

            if self._engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT:
                self._inputs.append({"host": host_mem, "device": device_mem, "shape": shape})
            else:
                self._outputs.append({"host": host_mem, "device": device_mem, "shape": shape})

    def unload(self) -> None:
        """Unload model resources."""
        self._ultralytics_model = None
        self._is_loaded = False

    def preprocess(self, image: NDArray) -> NDArray:
        """Preprocess image for YOLOv12 inference."""
        # Resize with letterbox
        img, ratio, pad = self._letterbox(
            image,
            new_shape=self.input_size,
            auto=False,
            stride=32,
        )

        # Store for postprocessing
        self._ratio = ratio
        self._pad = pad
        self._original_shape = image.shape[:2]

        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # HWC to CHW, normalize
        img = img.transpose(2, 0, 1).astype(np.float32) / 255.0

        # Add batch dimension
        img = np.expand_dims(img, 0)

        # Convert to half precision if needed
        if self.half_precision:
            img = img.astype(np.float16)

        return np.ascontiguousarray(img)

    def _letterbox(
        self,
        img: NDArray,
        new_shape: tuple[int, int] = (640, 640),
        color: tuple[int, int, int] = (114, 114, 114),
        auto: bool = True,
        stride: int = 32,
    ) -> tuple[NDArray, tuple[float, float], tuple[float, float]]:
        """Resize and pad image while meeting stride constraints."""
        shape = img.shape[:2]  # current hw

        # Scale ratio (new / old)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

        # Compute padding
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]

        if auto:
            dw, dh = np.mod(dw, stride), np.mod(dh, stride)

        dw /= 2
        dh /= 2

        if shape[::-1] != new_unpad:
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)

        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)

        return img, (r, r), (dw, dh)

    def forward(self, inputs: NDArray) -> NDArray:
        """Run YOLOv12 inference."""
        if self._ultralytics_model is not None:
            return self._forward_ultralytics(inputs)
        else:
            return self._forward_tensorrt(inputs)

    def _forward_ultralytics(self, inputs: NDArray) -> list:
        """Run inference via Ultralytics."""
        # Convert back to image format for Ultralytics
        img = (inputs[0].transpose(1, 2, 0) * 255).astype(np.uint8)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        results = self._ultralytics_model.predict(
            img,
            conf=self.conf_threshold,
            iou=self.nms_threshold,
            verbose=False,
        )
        return results

    def _forward_tensorrt(self, inputs: NDArray) -> NDArray:
        """Run TensorRT inference."""
        import pycuda.driver as cuda

        # Copy input to device
        np.copyto(self._inputs[0]["host"], inputs.ravel())
        cuda.memcpy_htod_async(
            self._inputs[0]["device"],
            self._inputs[0]["host"],
            self._stream,
        )

        # Execute
        self._context.execute_async_v2(
            bindings=self._bindings,
            stream_handle=self._stream.handle,
        )

        # Copy output from device
        cuda.memcpy_dtoh_async(
            self._outputs[0]["host"],
            self._outputs[0]["device"],
            self._stream,
        )
        self._stream.synchronize()

        return self._outputs[0]["host"].reshape(self._outputs[0]["shape"])

    def postprocess(
        self,
        outputs: list | NDArray,
        original_shape: tuple[int, int],
    ) -> list[Detection]:
        """Convert model outputs to Detection objects."""
        detections = []

        if self._ultralytics_model is not None:
            detections = self._postprocess_ultralytics(outputs)
        else:
            detections = self._postprocess_tensorrt(outputs, original_shape)

        return detections

    def _postprocess_ultralytics(self, results: list) -> list[Detection]:
        """Process Ultralytics results."""
        detections = []

        if not results or len(results) == 0:
            return detections

        result = results[0]

        if result.boxes is None:
            return detections

        boxes = result.boxes.xyxy.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy().astype(int)

        for box, conf, cls_id in zip(boxes, confs, classes):
            if conf < self.conf_threshold:
                continue

            class_name = self._get_class_name(cls_id)

            detection = Detection(
                class_id=int(cls_id),
                class_name=class_name,
                confidence=float(conf),
                bbox=BoundingBox(
                    x1=float(box[0]),
                    y1=float(box[1]),
                    x2=float(box[2]),
                    y2=float(box[3]),
                ),
            )
            detections.append(detection)

        return detections

    def _postprocess_tensorrt(
        self,
        outputs: NDArray,
        original_shape: tuple[int, int],
    ) -> list[Detection]:
        """Process TensorRT outputs."""
        detections = []

        # YOLOv12 output format: [batch, num_detections, 4 + num_classes]
        # or [batch, 4 + num_classes, num_detections] depending on export

        predictions = outputs[0]  # Remove batch dimension

        # Transpose if needed (detect format)
        if predictions.shape[0] == (4 + len(self.classes)):
            predictions = predictions.T

        for pred in predictions:
            # Extract box and confidence
            box = pred[:4]
            confidences = pred[4:]

            # Get max confidence class
            class_id = np.argmax(confidences)
            confidence = confidences[class_id]

            if confidence < self.conf_threshold:
                continue

            # Convert from center format to corner format
            cx, cy, w, h = box
            x1 = cx - w / 2
            y1 = cy - h / 2
            x2 = cx + w / 2
            y2 = cy + h / 2

            # Scale back to original image
            x1 = (x1 - self._pad[0]) / self._ratio[0]
            y1 = (y1 - self._pad[1]) / self._ratio[1]
            x2 = (x2 - self._pad[0]) / self._ratio[0]
            y2 = (y2 - self._pad[1]) / self._ratio[1]

            # Clip to image bounds
            x1 = max(0, min(x1, original_shape[1]))
            y1 = max(0, min(y1, original_shape[0]))
            x2 = max(0, min(x2, original_shape[1]))
            y2 = max(0, min(y2, original_shape[0]))

            detection = Detection(
                class_id=int(class_id),
                class_name=self._get_class_name(class_id),
                confidence=float(confidence),
                bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
            )
            detections.append(detection)

        # Apply NMS
        detections = self._nms(detections)

        return detections

    def _get_class_name(self, class_id: int) -> str:
        """Get class name from ID."""
        if 0 <= class_id < len(self.classes):
            return self.classes[class_id]
        return f"class_{class_id}"

    def _nms(self, detections: list[Detection]) -> list[Detection]:
        """Apply Non-Maximum Suppression."""
        if not detections:
            return []

        boxes = np.array([d.bbox.to_xyxy() for d in detections])
        scores = np.array([d.confidence for d in detections])
        class_ids = np.array([d.class_id for d in detections])

        # NMS per class
        keep_indices = []
        for class_id in np.unique(class_ids):
            class_mask = class_ids == class_id
            class_boxes = boxes[class_mask]
            class_scores = scores[class_mask]
            class_indices = np.where(class_mask)[0]

            # OpenCV NMS
            indices = cv2.dnn.NMSBoxes(
                class_boxes.tolist(),
                class_scores.tolist(),
                self.conf_threshold,
                self.nms_threshold,
            )

            if len(indices) > 0:
                keep_indices.extend(class_indices[indices.flatten()])

        return [detections[i] for i in keep_indices]

    def detect_with_tracking(
        self,
        image: NDArray,
        tracker_id: Optional[int] = None,
    ) -> list[Detection]:
        """Run detection with object tracking."""
        if self._ultralytics_model is None:
            return self(image)

        results = self._ultralytics_model.track(
            image,
            conf=self.conf_threshold,
            iou=self.nms_threshold,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False,
        )

        detections = []
        if results and results[0].boxes is not None:
            boxes = results[0].boxes

            for i in range(len(boxes)):
                box = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i].cpu().numpy())
                cls_id = int(boxes.cls[i].cpu().numpy())
                track_id = int(boxes.id[i].cpu().numpy()) if boxes.id is not None else None

                detection = Detection(
                    class_id=cls_id,
                    class_name=self._get_class_name(cls_id),
                    confidence=conf,
                    bbox=BoundingBox(
                        x1=float(box[0]),
                        y1=float(box[1]),
                        x2=float(box[2]),
                        y2=float(box[3]),
                    ),
                    track_id=track_id,
                )
                detections.append(detection)

        return detections
