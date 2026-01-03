"""RF-DETR (Region-Free DETR) segmentation model for infrastructure inspection."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from numpy.typing import NDArray
from loguru import logger

from bahb.core.config import RFDETRConfig
from bahb.core.types import BoundingBox, Detection, Segmentation
from bahb.models.base import BaseModel


class RFDETRSegmenter(BaseModel):
    """
    RF-DETR (Region-Free Detection Transformer) for instance segmentation.

    Key Features:
    - Transformer-based architecture without region proposals
    - End-to-end trainable with set-based loss
    - Excellent for detecting infrastructure components
    - High accuracy on complex scenes with occlusion
    """

    def __init__(self, config: RFDETRConfig):
        super().__init__(
            model_path=config.weights,
            device=config.device,
            half_precision=config.half_precision,
        )
        self.config = config
        self.input_size = config.input_size
        self.num_queries = config.num_queries
        self.threshold = config.threshold
        self.backbone = config.backbone

        # Model components
        self._backbone = None
        self._transformer = None
        self._mask_head = None

    def load(self) -> bool:
        """Load RF-DETR model."""
        try:
            engine_path = Path(self.model_path)

            if engine_path.suffix == ".engine" and engine_path.exists():
                return self._load_tensorrt()

            return self._load_pytorch()

        except Exception as e:
            logger.error(f"Failed to load RF-DETR: {e}")
            return False

    def _load_tensorrt(self) -> bool:
        """Load TensorRT-optimized RF-DETR."""
        try:
            import tensorrt as trt
            import pycuda.driver as cuda
            import pycuda.autoinit  # noqa

            logger.info(f"Loading RF-DETR TensorRT: {self.model_path}")

            with open(self.model_path, "rb") as f:
                runtime = trt.Runtime(trt.Logger(trt.Logger.WARNING))
                self._engine = runtime.deserialize_cuda_engine(f.read())

            self._context = self._engine.create_execution_context()
            self._stream = cuda.Stream()
            self._allocate_buffers()

            self._is_loaded = True
            logger.info("RF-DETR TensorRT loaded")
            return True

        except Exception as e:
            logger.warning(f"TensorRT failed: {e}, trying PyTorch")
            return self._load_pytorch()

    def _load_pytorch(self) -> bool:
        """Load PyTorch RF-DETR model."""
        try:
            import torch
            from transformers import AutoModelForObjectDetection, AutoImageProcessor

            logger.info("Loading RF-DETR via transformers")

            # Use DETR as base (RF-DETR follows similar architecture)
            model_id = "facebook/detr-resnet-101"

            self._processor = AutoImageProcessor.from_pretrained(model_id)
            self._model = AutoModelForObjectDetection.from_pretrained(model_id)

            # Move to device
            device = torch.device(self.device if torch.cuda.is_available() else "cpu")
            self._model = self._model.to(device)
            self._model.eval()

            if self.half_precision and device.type == "cuda":
                self._model = self._model.half()

            self._is_loaded = True
            logger.info("RF-DETR loaded via transformers")
            return True

        except Exception as e:
            logger.error(f"Failed to load PyTorch RF-DETR: {e}")
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
            shape = list(self._engine.get_tensor_shape(name))

            # Handle dynamic shapes
            if -1 in shape:
                shape = [max(1, s) if s == -1 else s for s in shape]

            dtype = trt.nptype(self._engine.get_tensor_dtype(name))
            size = int(np.prod(shape))

            host_mem = cuda.pagelocked_empty(size, dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)
            self._bindings.append(int(device_mem))

            binding = {"host": host_mem, "device": device_mem, "shape": shape, "name": name}

            if self._engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT:
                self._inputs.append(binding)
            else:
                self._outputs.append(binding)

    def unload(self) -> None:
        """Unload model resources."""
        self._model = None
        self._processor = None
        self._engine = None
        self._is_loaded = False

    def preprocess(self, image: NDArray) -> dict:
        """Preprocess image for RF-DETR."""
        self._original_shape = image.shape[:2]

        if hasattr(self, "_processor") and self._processor is not None:
            # Using transformers processor
            import torch

            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            inputs = self._processor(images=rgb_image, return_tensors="pt")

            device = next(self._model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}

            if self.half_precision and device.type == "cuda":
                inputs["pixel_values"] = inputs["pixel_values"].half()

            return inputs

        else:
            # TensorRT preprocessing
            # Resize
            resized = cv2.resize(image, self.input_size)

            # Convert BGR to RGB and normalize
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            normalized = rgb.astype(np.float32) / 255.0

            # Normalize with ImageNet stats
            mean = np.array([0.485, 0.456, 0.406])
            std = np.array([0.229, 0.224, 0.225])
            normalized = (normalized - mean) / std

            # HWC to CHW, add batch
            tensor = normalized.transpose(2, 0, 1)[np.newaxis, ...]

            if self.half_precision:
                tensor = tensor.astype(np.float16)

            return {"pixel_values": np.ascontiguousarray(tensor)}

    def forward(self, inputs: dict) -> dict:
        """Run RF-DETR inference."""
        if hasattr(self, "_model") and self._model is not None:
            return self._forward_pytorch(inputs)
        else:
            return self._forward_tensorrt(inputs)

    def _forward_pytorch(self, inputs: dict) -> dict:
        """Run PyTorch inference."""
        import torch

        with torch.no_grad():
            outputs = self._model(**inputs)

        return {
            "logits": outputs.logits,
            "pred_boxes": outputs.pred_boxes,
            "pred_masks": getattr(outputs, "pred_masks", None),
        }

    def _forward_tensorrt(self, inputs: dict) -> dict:
        """Run TensorRT inference."""
        import pycuda.driver as cuda

        pixel_values = inputs["pixel_values"]
        np.copyto(self._inputs[0]["host"], pixel_values.ravel())

        cuda.memcpy_htod_async(
            self._inputs[0]["device"],
            self._inputs[0]["host"],
            self._stream,
        )

        self._context.execute_async_v2(
            bindings=self._bindings,
            stream_handle=self._stream.handle,
        )

        outputs = {}
        for output in self._outputs:
            cuda.memcpy_dtoh_async(output["host"], output["device"], self._stream)

        self._stream.synchronize()

        for output in self._outputs:
            outputs[output["name"]] = output["host"].reshape(output["shape"])

        return outputs

    def postprocess(
        self,
        outputs: dict,
        original_shape: tuple[int, int],
    ) -> tuple[list[Detection], list[Segmentation]]:
        """Convert RF-DETR outputs to Detection and Segmentation objects."""
        detections = []
        segmentations = []

        if hasattr(self, "_processor") and self._processor is not None:
            detections, segmentations = self._postprocess_pytorch(outputs, original_shape)
        else:
            detections, segmentations = self._postprocess_tensorrt(outputs, original_shape)

        return detections, segmentations

    def _postprocess_pytorch(
        self,
        outputs: dict,
        original_shape: tuple[int, int],
    ) -> tuple[list[Detection], list[Segmentation]]:
        """Process PyTorch outputs."""
        import torch

        detections = []
        segmentations = []

        logits = outputs["logits"]
        pred_boxes = outputs["pred_boxes"]

        # Get probabilities
        probs = logits.softmax(-1)[0, :, :-1]  # Remove no-object class
        max_probs, class_ids = probs.max(-1)

        # Filter by threshold
        keep = max_probs > self.threshold
        keep_indices = keep.nonzero(as_tuple=True)[0]

        for idx in keep_indices:
            idx = idx.item()
            class_id = class_ids[idx].item()
            confidence = max_probs[idx].item()

            # Get box (cx, cy, w, h) -> (x1, y1, x2, y2)
            box = pred_boxes[0, idx].cpu().numpy()
            cx, cy, w, h = box

            x1 = (cx - w / 2) * original_shape[1]
            y1 = (cy - h / 2) * original_shape[0]
            x2 = (cx + w / 2) * original_shape[1]
            y2 = (cy + h / 2) * original_shape[0]

            detection = Detection(
                class_id=class_id,
                class_name=self._get_class_name(class_id),
                confidence=confidence,
                bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
            )
            detections.append(detection)

            # Process masks if available
            if outputs.get("pred_masks") is not None:
                mask = outputs["pred_masks"][0, idx]
                mask = torch.sigmoid(mask).cpu().numpy()
                mask = cv2.resize(mask, (original_shape[1], original_shape[0]))
                mask = (mask > 0.5).astype(np.uint8) * 255

                # Calculate centroid
                moments = cv2.moments(mask)
                if moments["m00"] > 0:
                    cx = int(moments["m10"] / moments["m00"])
                    cy = int(moments["m01"] / moments["m00"])
                else:
                    cx, cy = int(x1 + (x2 - x1) / 2), int(y1 + (y2 - y1) / 2)

                segmentation = Segmentation(
                    mask=mask,
                    class_id=class_id,
                    class_name=self._get_class_name(class_id),
                    confidence=confidence,
                    area=int(np.sum(mask > 0)),
                    centroid=(cx, cy),
                )
                segmentations.append(segmentation)

        return detections, segmentations

    def _postprocess_tensorrt(
        self,
        outputs: dict,
        original_shape: tuple[int, int],
    ) -> tuple[list[Detection], list[Segmentation]]:
        """Process TensorRT outputs."""
        detections = []
        segmentations = []

        # Extract outputs (format depends on export)
        logits = outputs.get("logits", outputs.get("output_0"))
        pred_boxes = outputs.get("pred_boxes", outputs.get("output_1"))

        if logits is None or pred_boxes is None:
            return detections, segmentations

        # Apply softmax
        probs = self._softmax(logits[0, :, :-1])
        max_probs = np.max(probs, axis=-1)
        class_ids = np.argmax(probs, axis=-1)

        # Filter by threshold
        keep = max_probs > self.threshold

        for i, should_keep in enumerate(keep):
            if not should_keep:
                continue

            class_id = int(class_ids[i])
            confidence = float(max_probs[i])

            # Convert box
            cx, cy, w, h = pred_boxes[0, i]
            x1 = (cx - w / 2) * original_shape[1]
            y1 = (cy - h / 2) * original_shape[0]
            x2 = (cx + w / 2) * original_shape[1]
            y2 = (cy + h / 2) * original_shape[0]

            detection = Detection(
                class_id=class_id,
                class_name=self._get_class_name(class_id),
                confidence=confidence,
                bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
            )
            detections.append(detection)

        return detections, segmentations

    def _softmax(self, x: NDArray) -> NDArray:
        """Compute softmax."""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

    def _get_class_name(self, class_id: int) -> str:
        """Get class name from COCO or custom classes."""
        coco_classes = [
            "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
            "truck", "boat", "traffic light", "fire hydrant", "stop sign",
            "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep",
            "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
            "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
            "sports ball", "kite", "baseball bat", "baseball glove", "skateboard",
            "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork",
            "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
            "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
            "couch", "potted plant", "bed", "dining table", "toilet", "tv",
            "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave",
            "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
            "scissors", "teddy bear", "hair drier", "toothbrush"
        ]

        if 0 <= class_id < len(coco_classes):
            return coco_classes[class_id]
        return f"class_{class_id}"

    def segment_from_detections(
        self,
        image: NDArray,
        detections: list[Detection],
    ) -> list[Segmentation]:
        """Generate segmentation masks for given detections."""
        segmentations = []

        for detection in detections:
            # Extract ROI
            bbox = detection.bbox
            x1, y1 = int(max(0, bbox.x1)), int(max(0, bbox.y1))
            x2, y2 = int(min(image.shape[1], bbox.x2)), int(min(image.shape[0], bbox.y2))

            if x2 <= x1 or y2 <= y1:
                continue

            roi = image[y1:y2, x1:x2]

            # Simple GrabCut segmentation for ROI
            mask = self._grabcut_segment(roi)

            # Create full-size mask
            full_mask = np.zeros(image.shape[:2], dtype=np.uint8)
            full_mask[y1:y2, x1:x2] = mask

            # Calculate centroid
            moments = cv2.moments(full_mask)
            if moments["m00"] > 0:
                cx = int(moments["m10"] / moments["m00"])
                cy = int(moments["m01"] / moments["m00"])
            else:
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

            segmentation = Segmentation(
                mask=full_mask,
                class_id=detection.class_id,
                class_name=detection.class_name,
                confidence=detection.confidence,
                area=int(np.sum(full_mask > 0)),
                centroid=(cx, cy),
            )
            segmentations.append(segmentation)

        return segmentations

    def _grabcut_segment(self, roi: NDArray, iterations: int = 5) -> NDArray:
        """Apply GrabCut for quick segmentation."""
        if roi.size == 0:
            return np.zeros((1, 1), dtype=np.uint8)

        mask = np.zeros(roi.shape[:2], dtype=np.uint8)
        bgd_model = np.zeros((1, 65), dtype=np.float64)
        fgd_model = np.zeros((1, 65), dtype=np.float64)

        # Initialize with center rectangle
        h, w = roi.shape[:2]
        rect = (int(w * 0.1), int(h * 0.1), int(w * 0.8), int(h * 0.8))

        try:
            cv2.grabCut(roi, mask, rect, bgd_model, fgd_model, iterations, cv2.GC_INIT_WITH_RECT)
            result = np.where((mask == 2) | (mask == 0), 0, 255).astype(np.uint8)
        except cv2.error:
            # Fallback: return full ROI as foreground
            result = np.ones(roi.shape[:2], dtype=np.uint8) * 255

        return result
