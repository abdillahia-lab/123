"""
Solar Defect Detector - YOLOv12-based solar panel defect detection.

Detects:
- Cell cracks and micro-cracks
- Hotspots
- Snail trails
- Delamination
- Soiling and bird droppings
- Broken glass
- Junction box issues
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from numpy.typing import NDArray
from loguru import logger

from paces.core.config import PacesConfig


class SolarDefectDetector:
    """
    YOLOv12-based solar panel defect detector.

    Optimized for:
    - TensorRT inference on NVIDIA GPUs
    - Real-time drone footage processing
    - Multi-scale defect detection
    """

    # Solar-specific detection classes
    CLASSES = [
        "cell_crack",
        "micro_crack",
        "hotspot",
        "snail_trail",
        "delamination",
        "discoloration",
        "soiling",
        "bird_droppings",
        "broken_glass",
        "junction_box_damage",
        "connector_damage",
        "frame_damage",
        "vegetation_shading",
        "dust_accumulation",
        "moisture_ingress",
    ]

    def __init__(self, config: PacesConfig):
        self.config = config
        self.model_config = config.models.yolov12

        self._model = None
        self._is_loaded = False

    async def load(self) -> bool:
        """Load the YOLOv12 model."""
        logger.info("Loading YOLOv12 solar defect detector...")

        try:
            # In production, this would load the actual TensorRT engine
            # For now, we simulate model loading

            model_path = Path(self.model_config.weights_solar)
            logger.info(f"Model path: {model_path}")

            # Simulated model loading
            self._model = self._create_mock_model()
            self._is_loaded = True

            logger.info("YOLOv12 solar detector loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load YOLOv12 model: {e}")
            return False

    def _create_mock_model(self):
        """Create a mock model for development."""
        class MockModel:
            def __call__(self, image):
                # Return empty detections for mock
                return []
        return MockModel()

    async def detect(
        self,
        image: NDArray[np.uint8],
        confidence_threshold: float = None,
    ) -> list[dict]:
        """
        Detect defects in a solar panel image.

        Args:
            image: RGB image array
            confidence_threshold: Override default threshold

        Returns:
            List of detection dictionaries
        """
        if not self._is_loaded:
            raise RuntimeError("Model not loaded")

        threshold = confidence_threshold or self.model_config.confidence_threshold

        # Preprocess
        processed = self._preprocess(image)

        # Run inference
        raw_detections = self._inference(processed)

        # Post-process
        detections = self._postprocess(raw_detections, image.shape, threshold)

        return detections

    def _preprocess(self, image: NDArray) -> NDArray:
        """Preprocess image for inference."""
        import cv2

        # Resize to model input size
        target_size = self.model_config.input_size
        resized = cv2.resize(image, target_size)

        # Normalize to 0-1
        normalized = resized.astype(np.float32) / 255.0

        # Convert to CHW format
        chw = np.transpose(normalized, (2, 0, 1))

        # Add batch dimension
        batched = np.expand_dims(chw, axis=0)

        return batched

    def _inference(self, processed: NDArray) -> list:
        """Run model inference."""
        if self._model is None:
            return []

        try:
            # In production, this calls the TensorRT engine
            results = self._model(processed)
            return results
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return []

    def _postprocess(
        self,
        raw_detections: list,
        original_shape: tuple,
        threshold: float,
    ) -> list[dict]:
        """Post-process model outputs."""
        detections = []

        for det in raw_detections:
            if det.get("confidence", 0) < threshold:
                continue

            # Scale bounding box to original image size
            bbox = self._scale_bbox(
                det["bbox"],
                self.model_config.input_size,
                original_shape[:2],
            )

            detection = {
                "class_id": det["class_id"],
                "class_name": self.CLASSES[det["class_id"]] if det["class_id"] < len(self.CLASSES) else "unknown",
                "confidence": det["confidence"],
                "bbox": bbox,
            }
            detections.append(detection)

        # Apply NMS
        detections = self._nms(detections, self.model_config.nms_threshold)

        return detections

    def _scale_bbox(
        self,
        bbox: tuple,
        from_size: tuple,
        to_size: tuple,
    ) -> tuple:
        """Scale bounding box from one size to another."""
        x1, y1, x2, y2 = bbox
        scale_x = to_size[1] / from_size[0]
        scale_y = to_size[0] / from_size[1]

        return (
            x1 * scale_x,
            y1 * scale_y,
            x2 * scale_x,
            y2 * scale_y,
        )

    def _nms(self, detections: list[dict], threshold: float) -> list[dict]:
        """Apply Non-Maximum Suppression."""
        if not detections:
            return []

        # Sort by confidence
        detections = sorted(detections, key=lambda x: x["confidence"], reverse=True)

        keep = []
        while detections:
            best = detections.pop(0)
            keep.append(best)

            detections = [
                d for d in detections
                if self._iou(best["bbox"], d["bbox"]) < threshold
            ]

        return keep

    def _iou(self, box1: tuple, box2: tuple) -> float:
        """Calculate Intersection over Union."""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        xi1 = max(x1_1, x1_2)
        yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2)
        yi2 = min(y2_1, y2_2)

        if xi2 < xi1 or yi2 < yi1:
            return 0.0

        inter_area = (xi2 - xi1) * (yi2 - yi1)
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)

        union_area = box1_area + box2_area - inter_area

        return inter_area / union_area if union_area > 0 else 0.0

    async def detect_batch(
        self,
        images: list[NDArray[np.uint8]],
    ) -> list[list[dict]]:
        """Detect defects in a batch of images."""
        results = []
        for image in images:
            detections = await self.detect(image)
            results.append(detections)
        return results

    async def unload(self) -> None:
        """Unload model and free resources."""
        logger.info("Unloading YOLOv12 solar detector")
        self._model = None
        self._is_loaded = False
