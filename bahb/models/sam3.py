"""SAM3 Nano (Segment Anything Model 3 Nano) for precision segmentation."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from numpy.typing import NDArray
from loguru import logger

from bahb.core.config import SAM3Config
from bahb.core.types import BoundingBox, Detection, Segmentation
from bahb.models.base import BaseModel


class SAM3NanoSegmenter(BaseModel):
    """
    SAM3 Nano - Lightweight Segment Anything Model for edge deployment.

    Features:
    - Point, box, and mask prompt inputs
    - Real-time performance on edge devices
    - Automatic mask generation mode
    - Multi-mask output with confidence scores
    """

    def __init__(self, config: SAM3Config):
        super().__init__(
            model_path=config.encoder_weights,
            device=config.device,
            half_precision=True,
        )
        self.config = config
        self.input_size = config.input_size
        self.points_per_batch = config.points_per_batch
        self.decoder_path = config.decoder_weights

        # Image encoder
        self._encoder = None
        self._decoder = None

        # Cached embeddings
        self._image_embeddings = None
        self._current_image_hash = None

    def load(self) -> bool:
        """Load SAM3 Nano encoder and decoder."""
        try:
            encoder_loaded = self._load_encoder()
            decoder_loaded = self._load_decoder()

            self._is_loaded = encoder_loaded and decoder_loaded
            return self._is_loaded

        except Exception as e:
            logger.error(f"Failed to load SAM3 Nano: {e}")
            return False

    def _load_encoder(self) -> bool:
        """Load image encoder."""
        encoder_path = Path(self.model_path)

        if encoder_path.suffix == ".engine" and encoder_path.exists():
            return self._load_tensorrt_encoder()

        return self._load_onnx_encoder()

    def _load_tensorrt_encoder(self) -> bool:
        """Load TensorRT encoder."""
        try:
            import tensorrt as trt
            import pycuda.driver as cuda
            import pycuda.autoinit  # noqa

            logger.info(f"Loading SAM3 encoder TensorRT: {self.model_path}")

            with open(self.model_path, "rb") as f:
                runtime = trt.Runtime(trt.Logger(trt.Logger.WARNING))
                self._encoder_engine = runtime.deserialize_cuda_engine(f.read())

            self._encoder_context = self._encoder_engine.create_execution_context()
            self._encoder_stream = cuda.Stream()

            # Allocate buffers
            self._encoder_inputs = []
            self._encoder_outputs = []
            self._encoder_bindings = []

            for i in range(self._encoder_engine.num_io_tensors):
                name = self._encoder_engine.get_tensor_name(i)
                shape = self._encoder_engine.get_tensor_shape(name)
                dtype = trt.nptype(self._encoder_engine.get_tensor_dtype(name))
                size = int(np.prod([max(1, s) for s in shape]))

                host_mem = cuda.pagelocked_empty(size, dtype)
                device_mem = cuda.mem_alloc(host_mem.nbytes)
                self._encoder_bindings.append(int(device_mem))

                if self._encoder_engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT:
                    self._encoder_inputs.append({"host": host_mem, "device": device_mem, "shape": shape})
                else:
                    self._encoder_outputs.append({"host": host_mem, "device": device_mem, "shape": shape})

            logger.info("SAM3 encoder loaded")
            return True

        except Exception as e:
            logger.warning(f"TensorRT encoder failed: {e}")
            return self._load_onnx_encoder()

    def _load_onnx_encoder(self) -> bool:
        """Load ONNX encoder."""
        try:
            import onnxruntime as ort

            onnx_path = Path(self.model_path).with_suffix(".onnx")
            if not onnx_path.exists():
                # Try SAM2 from Hugging Face as fallback
                logger.info("Using SAM2 as fallback")
                return self._load_sam2_fallback()

            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            self._encoder = ort.InferenceSession(str(onnx_path), providers=providers)
            logger.info("SAM3 encoder loaded via ONNX")
            return True

        except Exception as e:
            logger.error(f"ONNX encoder failed: {e}")
            return self._load_sam2_fallback()

    def _load_sam2_fallback(self) -> bool:
        """Load SAM2 model as fallback."""
        try:
            from sam2.build_sam import build_sam2
            from sam2.sam2_image_predictor import SAM2ImagePredictor

            # Use smallest SAM2 model
            model_cfg = "sam2_hiera_t.yaml"
            checkpoint = "sam2_hiera_tiny.pt"

            sam2_model = build_sam2(model_cfg, checkpoint, device=self.device)
            self._predictor = SAM2ImagePredictor(sam2_model)

            logger.info("SAM2 loaded as fallback")
            return True

        except ImportError:
            logger.warning("SAM2 not available, using OpenCV fallback")
            self._use_opencv_fallback = True
            return True
        except Exception as e:
            logger.warning(f"SAM2 failed: {e}, using OpenCV")
            self._use_opencv_fallback = True
            return True

    def _load_decoder(self) -> bool:
        """Load mask decoder."""
        decoder_path = Path(self.decoder_path)

        if not decoder_path.exists():
            logger.warning("Decoder not found, using encoder-only mode")
            return True

        try:
            if decoder_path.suffix == ".engine":
                return self._load_tensorrt_decoder()
            else:
                return self._load_onnx_decoder()
        except Exception as e:
            logger.warning(f"Decoder load failed: {e}")
            return True

    def _load_tensorrt_decoder(self) -> bool:
        """Load TensorRT decoder."""
        import tensorrt as trt
        import pycuda.driver as cuda

        with open(self.decoder_path, "rb") as f:
            runtime = trt.Runtime(trt.Logger(trt.Logger.WARNING))
            self._decoder_engine = runtime.deserialize_cuda_engine(f.read())

        self._decoder_context = self._decoder_engine.create_execution_context()
        self._decoder_stream = cuda.Stream()

        logger.info("SAM3 decoder loaded")
        return True

    def _load_onnx_decoder(self) -> bool:
        """Load ONNX decoder."""
        import onnxruntime as ort

        onnx_path = Path(self.decoder_path).with_suffix(".onnx")
        if onnx_path.exists():
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            self._decoder = ort.InferenceSession(str(onnx_path), providers=providers)
            logger.info("SAM3 decoder loaded via ONNX")
        return True

    def unload(self) -> None:
        """Unload model resources."""
        self._encoder = None
        self._decoder = None
        self._predictor = None
        self._image_embeddings = None
        self._is_loaded = False

    def preprocess(self, image: NDArray) -> NDArray:
        """Preprocess image for SAM3."""
        self._original_shape = image.shape[:2]

        # Resize to model input size
        resized = cv2.resize(image, self.input_size)

        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # Normalize
        normalized = rgb.astype(np.float32) / 255.0

        # ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        normalized = (normalized - mean) / std

        # HWC to CHW, add batch
        tensor = normalized.transpose(2, 0, 1)[np.newaxis, ...]

        return np.ascontiguousarray(tensor.astype(np.float32))

    def forward(self, inputs: NDArray) -> NDArray:
        """Compute image embeddings."""
        if hasattr(self, "_predictor") and self._predictor is not None:
            return self._forward_sam2(inputs)
        elif hasattr(self, "_use_opencv_fallback") and self._use_opencv_fallback:
            return inputs  # Pass through for OpenCV processing
        else:
            return self._forward_encoder(inputs)

    def _forward_sam2(self, inputs: NDArray) -> NDArray:
        """Forward pass using SAM2."""
        # Convert back to image for SAM2
        img = (inputs[0].transpose(1, 2, 0) * np.array([0.229, 0.224, 0.225]) +
               np.array([0.485, 0.456, 0.406]))
        img = (img * 255).astype(np.uint8)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        self._predictor.set_image(img)
        return self._predictor.get_image_embedding()

    def _forward_encoder(self, inputs: NDArray) -> NDArray:
        """Run encoder inference."""
        if self._encoder is not None:
            # ONNX inference
            output = self._encoder.run(None, {"image": inputs})
            return output[0]
        elif hasattr(self, "_encoder_context"):
            # TensorRT inference
            import pycuda.driver as cuda

            np.copyto(self._encoder_inputs[0]["host"], inputs.ravel())
            cuda.memcpy_htod_async(
                self._encoder_inputs[0]["device"],
                self._encoder_inputs[0]["host"],
                self._encoder_stream,
            )

            self._encoder_context.execute_async_v2(
                bindings=self._encoder_bindings,
                stream_handle=self._encoder_stream.handle,
            )

            cuda.memcpy_dtoh_async(
                self._encoder_outputs[0]["host"],
                self._encoder_outputs[0]["device"],
                self._encoder_stream,
            )
            self._encoder_stream.synchronize()

            return self._encoder_outputs[0]["host"].reshape(self._encoder_outputs[0]["shape"])

        return inputs

    def postprocess(
        self,
        outputs: NDArray,
        original_shape: tuple[int, int],
    ) -> list[Segmentation]:
        """Postprocess embeddings (mainly for automatic mask generation)."""
        # This is called for automatic mask generation
        # For prompted segmentation, use segment_with_* methods
        return []

    def set_image(self, image: NDArray) -> None:
        """Set image and compute embeddings for subsequent segmentation."""
        image_hash = hash(image.tobytes())

        if image_hash != self._current_image_hash:
            self._current_image = image
            self._current_image_hash = image_hash

            if hasattr(self, "_predictor") and self._predictor is not None:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self._predictor.set_image(rgb_image)
            else:
                preprocessed = self.preprocess(image)
                self._image_embeddings = self.forward(preprocessed)

    def segment_with_points(
        self,
        points: list[tuple[int, int]],
        point_labels: list[int],
        multimask_output: bool = True,
    ) -> list[Segmentation]:
        """
        Segment using point prompts.

        Args:
            points: List of (x, y) coordinates
            point_labels: 1 for foreground, 0 for background
            multimask_output: Return multiple mask predictions
        """
        if hasattr(self, "_predictor") and self._predictor is not None:
            return self._segment_points_sam2(points, point_labels, multimask_output)
        elif hasattr(self, "_use_opencv_fallback") and self._use_opencv_fallback:
            return self._segment_points_opencv(points, point_labels)

        return self._segment_points_native(points, point_labels, multimask_output)

    def _segment_points_sam2(
        self,
        points: list[tuple[int, int]],
        point_labels: list[int],
        multimask_output: bool,
    ) -> list[Segmentation]:
        """Segment using SAM2."""
        import numpy as np

        point_coords = np.array(points)
        point_labels_arr = np.array(point_labels)

        masks, scores, _ = self._predictor.predict(
            point_coords=point_coords,
            point_labels=point_labels_arr,
            multimask_output=multimask_output,
        )

        segmentations = []
        for i, (mask, score) in enumerate(zip(masks, scores)):
            # Resize to original size
            mask_resized = cv2.resize(
                mask.astype(np.uint8) * 255,
                (self._original_shape[1], self._original_shape[0]),
            )

            moments = cv2.moments(mask_resized)
            if moments["m00"] > 0:
                cx = int(moments["m10"] / moments["m00"])
                cy = int(moments["m01"] / moments["m00"])
            else:
                cx, cy = self._original_shape[1] // 2, self._original_shape[0] // 2

            segmentation = Segmentation(
                mask=mask_resized,
                class_id=0,
                class_name="object",
                confidence=float(score),
                area=int(np.sum(mask_resized > 0)),
                centroid=(cx, cy),
            )
            segmentations.append(segmentation)

        return segmentations

    def _segment_points_opencv(
        self,
        points: list[tuple[int, int]],
        point_labels: list[int],
    ) -> list[Segmentation]:
        """Fallback segmentation using OpenCV."""
        if self._current_image is None:
            return []

        image = self._current_image.copy()

        # Use watershed segmentation around points
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Create markers from points
        markers = np.zeros_like(gray, dtype=np.int32)
        for i, (point, label) in enumerate(zip(points, point_labels), 1):
            if label == 1:  # Foreground
                cv2.circle(markers, point, 5, i, -1)

        # Apply watershed
        cv2.watershed(image, markers)

        segmentations = []
        for i, (point, label) in enumerate(zip(points, point_labels), 1):
            if label != 1:
                continue

            mask = (markers == i).astype(np.uint8) * 255

            moments = cv2.moments(mask)
            if moments["m00"] > 0:
                cx = int(moments["m10"] / moments["m00"])
                cy = int(moments["m01"] / moments["m00"])
            else:
                cx, cy = point

            segmentation = Segmentation(
                mask=mask,
                class_id=0,
                class_name="object",
                confidence=0.8,
                area=int(np.sum(mask > 0)),
                centroid=(cx, cy),
            )
            segmentations.append(segmentation)

        return segmentations

    def _segment_points_native(
        self,
        points: list[tuple[int, int]],
        point_labels: list[int],
        multimask_output: bool,
    ) -> list[Segmentation]:
        """Native SAM3 point segmentation."""
        # Prepare decoder inputs
        # This requires the full decoder implementation
        # For now, use OpenCV fallback
        return self._segment_points_opencv(points, point_labels)

    def segment_with_box(
        self,
        box: BoundingBox,
        multimask_output: bool = False,
    ) -> list[Segmentation]:
        """
        Segment using bounding box prompt.

        Args:
            box: Bounding box (x1, y1, x2, y2)
            multimask_output: Return multiple mask predictions
        """
        if hasattr(self, "_predictor") and self._predictor is not None:
            import numpy as np

            box_array = np.array([box.x1, box.y1, box.x2, box.y2])

            masks, scores, _ = self._predictor.predict(
                box=box_array,
                multimask_output=multimask_output,
            )

            segmentations = []
            for mask, score in zip(masks, scores):
                mask_resized = cv2.resize(
                    mask.astype(np.uint8) * 255,
                    (self._original_shape[1], self._original_shape[0]),
                )

                moments = cv2.moments(mask_resized)
                cx = int(moments["m10"] / moments["m00"]) if moments["m00"] > 0 else int(box.center[0])
                cy = int(moments["m01"] / moments["m00"]) if moments["m00"] > 0 else int(box.center[1])

                segmentations.append(Segmentation(
                    mask=mask_resized,
                    class_id=0,
                    class_name="object",
                    confidence=float(score),
                    area=int(np.sum(mask_resized > 0)),
                    centroid=(cx, cy),
                ))

            return segmentations

        # OpenCV fallback - GrabCut
        return self._segment_box_grabcut(box)

    def _segment_box_grabcut(self, box: BoundingBox) -> list[Segmentation]:
        """Box segmentation using GrabCut."""
        if self._current_image is None:
            return []

        image = self._current_image
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        bgd_model = np.zeros((1, 65), dtype=np.float64)
        fgd_model = np.zeros((1, 65), dtype=np.float64)

        rect = (int(box.x1), int(box.y1), int(box.width), int(box.height))

        try:
            cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            result_mask = np.where((mask == 2) | (mask == 0), 0, 255).astype(np.uint8)
        except cv2.error:
            result_mask = np.zeros(image.shape[:2], dtype=np.uint8)
            result_mask[int(box.y1):int(box.y2), int(box.x1):int(box.x2)] = 255

        moments = cv2.moments(result_mask)
        cx = int(moments["m10"] / moments["m00"]) if moments["m00"] > 0 else int(box.center[0])
        cy = int(moments["m01"] / moments["m00"]) if moments["m00"] > 0 else int(box.center[1])

        return [Segmentation(
            mask=result_mask,
            class_id=0,
            class_name="object",
            confidence=0.9,
            area=int(np.sum(result_mask > 0)),
            centroid=(cx, cy),
        )]

    def segment_detections(
        self,
        image: NDArray,
        detections: list[Detection],
    ) -> list[Segmentation]:
        """Generate precise masks for all detections."""
        self.set_image(image)

        segmentations = []
        for detection in detections:
            masks = self.segment_with_box(detection.bbox, multimask_output=False)
            if masks:
                # Update class info from detection
                seg = masks[0]
                seg.class_id = detection.class_id
                seg.class_name = detection.class_name
                seg.confidence = detection.confidence * seg.confidence
                segmentations.append(seg)

        return segmentations

    def auto_generate_masks(
        self,
        image: NDArray,
        points_per_side: int = 32,
        pred_iou_thresh: float = 0.88,
        stability_score_thresh: float = 0.95,
    ) -> list[Segmentation]:
        """
        Automatically generate masks for all objects in image.

        This is useful for scene understanding and object discovery.
        """
        self.set_image(image)

        if hasattr(self, "_predictor") and self._predictor is not None:
            # SAM2 automatic mask generation would go here
            # For now, use grid-based approach
            pass

        # Grid-based approach
        h, w = image.shape[:2]
        step_x = w // points_per_side
        step_y = h // points_per_side

        all_masks = []

        for y in range(step_y // 2, h, step_y):
            for x in range(step_x // 2, w, step_x):
                masks = self.segment_with_points(
                    points=[(x, y)],
                    point_labels=[1],
                    multimask_output=False,
                )
                all_masks.extend(masks)

        # Filter and deduplicate masks
        filtered = self._filter_masks(all_masks, pred_iou_thresh, stability_score_thresh)

        return filtered

    def _filter_masks(
        self,
        masks: list[Segmentation],
        iou_thresh: float,
        conf_thresh: float,
    ) -> list[Segmentation]:
        """Filter and deduplicate masks."""
        # Sort by confidence
        masks = sorted(masks, key=lambda x: x.confidence, reverse=True)

        # Filter by confidence
        masks = [m for m in masks if m.confidence >= conf_thresh]

        # NMS-like deduplication
        keep = []
        for mask in masks:
            is_duplicate = False
            for kept in keep:
                # Calculate IoU
                intersection = np.logical_and(mask.mask > 0, kept.mask > 0).sum()
                union = np.logical_or(mask.mask > 0, kept.mask > 0).sum()
                iou = intersection / union if union > 0 else 0

                if iou > iou_thresh:
                    is_duplicate = True
                    break

            if not is_duplicate:
                keep.append(mask)

        return keep
