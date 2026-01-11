"""
Wind Turbine Blade Inspector - AI-powered blade defect detection.

Detects:
- Surface cracks
- Leading edge erosion
- Lightning strike damage
- Ice buildup
- Delamination
- Structural damage
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from uuid import uuid4

import numpy as np
from numpy.typing import NDArray
from loguru import logger

from paces.core.config import PacesConfig
from paces.core.types import AlertSeverity, Defect, DefectType, BoundingBox


class BladeInspector:
    """
    YOLOv12-based wind turbine blade inspector.

    Specialized for detecting blade surface and structural defects
    from drone imagery at various distances and angles.
    """

    CLASSES = [
        "blade_crack",
        "leading_edge_erosion",
        "trailing_edge_damage",
        "lightning_strike",
        "ice_buildup",
        "delamination",
        "surface_contamination",
        "paint_damage",
        "structural_crack",
        "tip_damage",
        "root_damage",
        "bond_line_failure",
        "vortex_generator_damage",
        "oil_stain",
    ]

    def __init__(self, config: PacesConfig):
        self.config = config
        self.model_config = config.models.yolov12

        self._model = None
        self._is_loaded = False

    async def load(self) -> bool:
        """Load the blade inspection model."""
        logger.info("Loading blade inspection model...")

        try:
            model_path = Path(self.model_config.weights_wind)
            logger.info(f"Model path: {model_path}")

            self._model = self._create_mock_model()
            self._is_loaded = True

            logger.info("Blade inspector loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load blade inspector: {e}")
            return False

    def _create_mock_model(self):
        """Create mock model for development."""
        class MockModel:
            def __call__(self, image):
                return []
        return MockModel()

    async def inspect(
        self,
        image: NDArray[np.uint8],
        blade_id: int = 0,
        turbine_id: str = "",
    ) -> dict:
        """
        Inspect a blade image for defects.

        Args:
            image: RGB image of blade
            blade_id: Blade identifier (0, 1, 2)
            turbine_id: Parent turbine ID

        Returns:
            Inspection result dictionary
        """
        if not self._is_loaded:
            raise RuntimeError("Model not loaded")

        # Preprocess
        processed = self._preprocess(image)

        # Run detection
        raw_detections = self._inference(processed)

        # Post-process
        detections = self._postprocess(raw_detections, image.shape)

        # Convert to defects
        defects = []
        for det in detections:
            defect = self._detection_to_defect(det, turbine_id, blade_id)
            defects.append(defect)

        # Analyze blade section
        sections = self._analyze_blade_sections(image, detections)

        return {
            "blade_id": blade_id,
            "defects": defects,
            "sections": sections,
            "overall_condition": self._assess_condition(defects),
        }

    def _preprocess(self, image: NDArray) -> NDArray:
        """Preprocess image for inference."""
        import cv2

        target_size = self.model_config.input_size
        resized = cv2.resize(image, target_size)
        normalized = resized.astype(np.float32) / 255.0
        chw = np.transpose(normalized, (2, 0, 1))
        batched = np.expand_dims(chw, axis=0)

        return batched

    def _inference(self, processed: NDArray) -> list:
        """Run model inference."""
        if self._model is None:
            return []

        try:
            return self._model(processed)
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return []

    def _postprocess(
        self,
        raw_detections: list,
        original_shape: tuple,
    ) -> list[dict]:
        """Post-process model outputs."""
        detections = []
        threshold = self.model_config.confidence_threshold

        for det in raw_detections:
            if det.get("confidence", 0) < threshold:
                continue

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

        return detections

    def _scale_bbox(
        self,
        bbox: tuple,
        from_size: tuple,
        to_size: tuple,
    ) -> tuple:
        """Scale bounding box."""
        x1, y1, x2, y2 = bbox
        scale_x = to_size[1] / from_size[0]
        scale_y = to_size[0] / from_size[1]
        return (x1 * scale_x, y1 * scale_y, x2 * scale_x, y2 * scale_y)

    def _detection_to_defect(
        self,
        detection: dict,
        turbine_id: str,
        blade_id: int,
    ) -> Defect:
        """Convert detection to Defect object."""
        defect_mapping = {
            "blade_crack": DefectType.BLADE_CRACK,
            "leading_edge_erosion": DefectType.BLADE_EROSION,
            "trailing_edge_damage": DefectType.BLADE_CRACK,
            "lightning_strike": DefectType.LIGHTNING_STRIKE,
            "ice_buildup": DefectType.ICE_BUILDUP,
            "delamination": DefectType.DELAMINATION,
            "structural_crack": DefectType.BLADE_CRACK,
        }

        defect_type = defect_mapping.get(
            detection["class_name"],
            DefectType.STRUCTURAL_DAMAGE
        )

        severity = self._classify_severity(
            detection["class_name"],
            detection["confidence"]
        )

        recommendations = self._get_recommendations(detection["class_name"])

        return Defect(
            id=str(uuid4())[:8],
            asset_id=f"{turbine_id}_blade_{blade_id}",
            defect_type=defect_type,
            severity=severity,
            confidence=detection["confidence"],
            bbox=BoundingBox(
                x1=detection["bbox"][0],
                y1=detection["bbox"][1],
                x2=detection["bbox"][2],
                y2=detection["bbox"][3],
            ),
            description=f"Blade {blade_id}: {defect_type.value.replace('_', ' ').title()}",
            recommendations=recommendations,
        )

    def _classify_severity(self, defect_class: str, confidence: float) -> AlertSeverity:
        """Classify defect severity."""
        critical_defects = {"structural_crack", "lightning_strike", "root_damage"}
        high_defects = {"blade_crack", "delamination", "bond_line_failure"}
        medium_defects = {"leading_edge_erosion", "trailing_edge_damage"}

        if defect_class in critical_defects:
            return AlertSeverity.CRITICAL
        elif defect_class in high_defects:
            return AlertSeverity.HIGH
        elif defect_class in medium_defects:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW

    def _get_recommendations(self, defect_class: str) -> list[str]:
        """Get recommendations for defect type."""
        recommendations = {
            "blade_crack": [
                "Immediate structural assessment required",
                "Consider blade replacement or repair",
                "Monitor crack propagation",
            ],
            "leading_edge_erosion": [
                "Schedule leading edge protection repair",
                "Consider LEP tape or coating application",
                "Monitor erosion progression",
            ],
            "lightning_strike": [
                "Full blade inspection required",
                "Check lightning protection system",
                "Assess internal structural damage",
            ],
            "ice_buildup": [
                "Activate de-icing system if available",
                "Consider curtailment until ice clears",
                "Check heating elements",
            ],
            "delamination": [
                "Assess delamination extent",
                "Schedule repair based on severity",
                "Monitor for moisture ingress",
            ],
        }
        return recommendations.get(defect_class, ["Document finding", "Schedule inspection"])

    def _analyze_blade_sections(
        self,
        image: NDArray,
        detections: list,
    ) -> dict:
        """Analyze blade sections (root, mid, tip)."""
        h, w = image.shape[:2]

        sections = {
            "root": {"x1": 0, "x2": w // 3, "defects": 0, "condition": "good"},
            "mid": {"x1": w // 3, "x2": 2 * w // 3, "defects": 0, "condition": "good"},
            "tip": {"x1": 2 * w // 3, "x2": w, "defects": 0, "condition": "good"},
        }

        for det in detections:
            cx = (det["bbox"][0] + det["bbox"][2]) / 2
            for section_name, section in sections.items():
                if section["x1"] <= cx < section["x2"]:
                    section["defects"] += 1

        # Assess condition
        for section in sections.values():
            if section["defects"] >= 3:
                section["condition"] = "poor"
            elif section["defects"] >= 1:
                section["condition"] = "fair"

        return sections

    def _assess_condition(self, defects: list[Defect]) -> str:
        """Assess overall blade condition."""
        critical = sum(1 for d in defects if d.severity == AlertSeverity.CRITICAL)
        high = sum(1 for d in defects if d.severity == AlertSeverity.HIGH)

        if critical > 0:
            return "critical"
        elif high > 0:
            return "poor"
        elif len(defects) > 3:
            return "fair"
        elif len(defects) > 0:
            return "acceptable"
        else:
            return "good"

    async def unload(self) -> None:
        """Unload model."""
        logger.info("Unloading blade inspector")
        self._model = None
        self._is_loaded = False
