"""Unified inference pipeline combining all AI models."""

from __future__ import annotations

import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

import numpy as np
from numpy.typing import NDArray
from loguru import logger

from bahb.core.config import Config, ModelsConfig
from bahb.core.types import (
    Anomaly,
    Detection,
    FrameData,
    GeoLocation,
    InspectionResult,
    Segmentation,
    SeverityLevel,
    ThermalReading,
)
from bahb.models.yolov12 import YOLOv12Detector
from bahb.models.rf_detr import RFDETRSegmenter
from bahb.models.sam3 import SAM3NanoSegmenter
from bahb.models.qwen_vl import QwenVLAnalyzer


@dataclass
class PipelineMetrics:
    """Performance metrics for the inference pipeline."""
    total_frames: int = 0
    total_detections: int = 0
    total_anomalies: int = 0

    # Timing (ms)
    avg_yolo_time: float = 0.0
    avg_rfdetr_time: float = 0.0
    avg_sam3_time: float = 0.0
    avg_qwen_time: float = 0.0
    avg_total_time: float = 0.0

    # Throughput
    fps: float = 0.0


class InferencePipeline:
    """
    Unified AI inference pipeline for infrastructure inspection.

    Pipeline flow:
    1. YOLOv12 - Fast object detection
    2. RF-DETR - Detailed segmentation (for key detections)
    3. SAM3 Nano - Precision masks (for anomalies)
    4. Qwen2.5-VL - Visual analysis and description

    The pipeline is designed for real-time performance on Manifold 3,
    with intelligent scheduling based on detection importance.
    """

    def __init__(self, config: Config):
        self.config = config
        self.models_config = config.models

        # Initialize models
        self.yolo: Optional[YOLOv12Detector] = None
        self.rf_detr: Optional[RFDETRSegmenter] = None
        self.sam3: Optional[SAM3NanoSegmenter] = None
        self.qwen_vl: Optional[QwenVLAnalyzer] = None

        # Thread pool for parallel inference
        self._executor = ThreadPoolExecutor(max_workers=4)

        # Metrics
        self._metrics = PipelineMetrics()
        self._timing_history: list[dict] = []
        self._fps_history: list[float] = []
        self._last_time = time.time()

        # Callbacks
        self._on_detection: Optional[Callable[[list[Detection]], None]] = None
        self._on_anomaly: Optional[Callable[[Anomaly], None]] = None
        self._on_result: Optional[Callable[[InspectionResult], None]] = None

        # Configuration
        self.enable_tracking = True
        self.vlm_analysis_interval = 5  # Analyze every N frames
        self.vlm_on_anomaly = True  # Always analyze frames with anomalies
        self._frame_count = 0

    async def initialize(self) -> bool:
        """Initialize all AI models."""
        logger.info("Initializing AI inference pipeline...")

        success = True

        # Load models in parallel
        load_tasks = []

        if self.models_config.yolov12.enabled:
            self.yolo = YOLOv12Detector(self.models_config.yolov12)
            load_tasks.append(("YOLOv12", self.yolo))

        if self.models_config.rf_detr.enabled:
            self.rf_detr = RFDETRSegmenter(self.models_config.rf_detr)
            load_tasks.append(("RF-DETR", self.rf_detr))

        if self.models_config.sam3_nano.enabled:
            self.sam3 = SAM3NanoSegmenter(self.models_config.sam3_nano)
            load_tasks.append(("SAM3-Nano", self.sam3))

        if self.models_config.qwen_vl.enabled:
            self.qwen_vl = QwenVLAnalyzer(self.models_config.qwen_vl)
            load_tasks.append(("Qwen-VL", self.qwen_vl))

        # Load each model
        for name, model in load_tasks:
            try:
                logger.info(f"Loading {name}...")
                if model.load():
                    logger.info(f"{name} loaded successfully")
                else:
                    logger.warning(f"{name} failed to load")
                    success = False
            except Exception as e:
                logger.error(f"Error loading {name}: {e}")
                success = False

        # Warmup models
        if success:
            await self._warmup_models()

        logger.info(f"Pipeline initialization {'complete' if success else 'failed'}")
        return success

    async def _warmup_models(self) -> None:
        """Warmup all models with dummy input."""
        dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)

        warmup_tasks = []
        if self.yolo and self.yolo.is_loaded:
            warmup_tasks.append(self._warmup_model(self.yolo, "YOLOv12"))
        if self.rf_detr and self.rf_detr.is_loaded:
            warmup_tasks.append(self._warmup_model(self.rf_detr, "RF-DETR"))
        if self.sam3 and self.sam3.is_loaded:
            warmup_tasks.append(self._warmup_model(self.sam3, "SAM3"))

        await asyncio.gather(*warmup_tasks)

    async def _warmup_model(self, model, name: str) -> None:
        """Warmup a single model."""
        try:
            model.warmup()
        except Exception as e:
            logger.warning(f"{name} warmup failed: {e}")

    def set_callbacks(
        self,
        on_detection: Optional[Callable[[list[Detection]], None]] = None,
        on_anomaly: Optional[Callable[[Anomaly], None]] = None,
        on_result: Optional[Callable[[InspectionResult], None]] = None,
    ) -> None:
        """Set callback functions for pipeline events."""
        self._on_detection = on_detection
        self._on_anomaly = on_anomaly
        self._on_result = on_result

    async def process_frame(
        self,
        frame_data: FrameData,
        thermal_data: Optional[ThermalReading] = None,
    ) -> InspectionResult:
        """
        Process a single frame through the full pipeline.

        Args:
            frame_data: Multi-sensor frame data
            thermal_data: Pre-computed thermal analysis

        Returns:
            InspectionResult with all findings
        """
        start_time = time.perf_counter()
        self._frame_count += 1

        # Use wide image as primary (or zoom if available)
        image = frame_data.wide_image
        if image is None:
            image = frame_data.zoom_image
        if image is None:
            logger.warning("No image available for processing")
            return InspectionResult(
                frame_id=frame_data.frame_id,
                timestamp=frame_data.timestamp,
                location=frame_data.location,
            )

        timing = {}

        # Stage 1: Fast detection with YOLOv12
        detections = []
        if self.yolo and self.yolo.is_loaded:
            yolo_start = time.perf_counter()

            if self.enable_tracking:
                detections = self.yolo.detect_with_tracking(image)
            else:
                detections = self.yolo(image)

            timing["yolo"] = (time.perf_counter() - yolo_start) * 1000

            if self._on_detection and detections:
                self._on_detection(detections)

        # Stage 2: Detailed segmentation for important objects
        segmentations = []
        if self.rf_detr and self.rf_detr.is_loaded and detections:
            rfdetr_start = time.perf_counter()

            # Filter to important detections for segmentation
            important = self._filter_important_detections(detections)
            if important:
                _, segs = self.rf_detr(image)
                segmentations = segs

            timing["rf_detr"] = (time.perf_counter() - rfdetr_start) * 1000

        # Stage 3: Precision masks for potential anomalies
        if self.sam3 and self.sam3.is_loaded:
            sam_start = time.perf_counter()

            # Find anomaly candidates (thermal hotspots + defect detections)
            anomaly_candidates = self._find_anomaly_candidates(detections, thermal_data)

            if anomaly_candidates:
                self.sam3.set_image(image)
                for det in anomaly_candidates:
                    masks = self.sam3.segment_with_box(det.bbox)
                    if masks:
                        det.mask = masks[0].mask

            timing["sam3"] = (time.perf_counter() - sam_start) * 1000

        # Stage 4: Anomaly detection and classification
        anomalies = self._detect_anomalies(
            image,
            detections,
            segmentations,
            thermal_data,
            frame_data.location,
        )

        # Trigger anomaly callbacks
        for anomaly in anomalies:
            if self._on_anomaly:
                self._on_anomaly(anomaly)

        # Stage 5: VLM analysis (conditional)
        vlm_description = None
        vlm_recommendations = None

        should_analyze = (
            self._frame_count % self.vlm_analysis_interval == 0 or
            (self.vlm_on_anomaly and any(a.severity.value >= SeverityLevel.MEDIUM.value for a in anomalies))
        )

        if self.qwen_vl and self.qwen_vl.is_loaded and should_analyze:
            vlm_start = time.perf_counter()

            # Determine prompt type
            if thermal_data and len(thermal_data.hotspot_locations) > 0:
                prompt_type = "thermal"
            elif any(d.class_name in ["transformer", "insulator", "switchgear"] for d in detections):
                prompt_type = "substation"
            elif any(d.class_name in ["server_rack", "hvac_unit", "cooling_fan"] for d in detections):
                prompt_type = "datacenter"
            else:
                prompt_type = "general"

            vlm_description = self.qwen_vl.analyze(image, prompt_type=prompt_type)

            # Extract recommendations from anomalies
            if anomalies:
                all_recommendations = []
                for anomaly in anomalies:
                    all_recommendations.extend(anomaly.recommendations)
                vlm_recommendations = list(set(all_recommendations))[:5]

            timing["qwen_vl"] = (time.perf_counter() - vlm_start) * 1000

        # Calculate total time
        total_time = (time.perf_counter() - start_time) * 1000
        timing["total"] = total_time

        # Update metrics
        self._update_metrics(timing, len(detections), len(anomalies))

        # Create result
        result = InspectionResult(
            frame_id=frame_data.frame_id,
            timestamp=frame_data.timestamp,
            location=frame_data.location,
            detections=detections,
            segmentations=segmentations,
            thermal_reading=thermal_data,
            anomalies=anomalies,
            vlm_description=vlm_description,
            vlm_recommendations=vlm_recommendations,
            inference_time_ms=total_time,
        )

        if self._on_result:
            self._on_result(result)

        return result

    def _filter_important_detections(
        self,
        detections: list[Detection],
        top_k: int = 10,
    ) -> list[Detection]:
        """Filter detections to most important for detailed analysis."""
        # Priority classes for infrastructure
        priority_classes = {
            "transformer", "insulator", "switchgear", "damage",
            "hotspot", "corrosion", "leak", "crack",
        }

        # Separate priority and other
        priority = [d for d in detections if d.class_name in priority_classes]
        other = [d for d in detections if d.class_name not in priority_classes]

        # Sort by confidence
        priority.sort(key=lambda x: x.confidence, reverse=True)
        other.sort(key=lambda x: x.confidence, reverse=True)

        # Take top detections
        result = priority[:top_k]
        remaining = top_k - len(result)
        if remaining > 0:
            result.extend(other[:remaining])

        return result

    def _find_anomaly_candidates(
        self,
        detections: list[Detection],
        thermal: Optional[ThermalReading],
    ) -> list[Detection]:
        """Find detections that might be anomalies."""
        candidates = []

        # Defect class detections
        defect_classes = {"damage", "corrosion", "hotspot", "leak", "crack", "contamination"}
        candidates.extend([d for d in detections if d.class_name in defect_classes])

        # High-confidence equipment near thermal hotspots
        if thermal and thermal.hotspot_locations:
            equipment_classes = {"transformer", "insulator", "switchgear", "conductor"}
            for det in detections:
                if det.class_name in equipment_classes:
                    # Check if any hotspot is within detection bbox
                    for hx, hy in thermal.hotspot_locations:
                        if (det.bbox.x1 <= hx <= det.bbox.x2 and
                            det.bbox.y1 <= hy <= det.bbox.y2):
                            candidates.append(det)
                            break

        return list(set(candidates))

    def _detect_anomalies(
        self,
        image: NDArray,
        detections: list[Detection],
        segmentations: list[Segmentation],
        thermal: Optional[ThermalReading],
        location: Optional[GeoLocation],
    ) -> list[Anomaly]:
        """Detect and classify anomalies from pipeline outputs."""
        anomalies = []

        # Direct defect detections
        defect_classes = {"damage", "corrosion", "hotspot", "leak", "crack", "contamination"}

        for det in detections:
            if det.class_name in defect_classes:
                # Get VLM description if available
                description = f"{det.class_name.title()} detected with {det.confidence:.1%} confidence"
                recommendations = self._get_default_recommendations(det.class_name)

                if self.qwen_vl and self.qwen_vl.is_loaded:
                    try:
                        desc, recs = self.qwen_vl.generate_anomaly_description(
                            image, det, thermal
                        )
                        description = desc
                        recommendations = recs
                    except Exception as e:
                        logger.warning(f"VLM description failed: {e}")

                # Determine severity
                severity = self._assess_severity(det, thermal)

                anomaly = Anomaly(
                    id=str(uuid.uuid4())[:8],
                    type=det.class_name,
                    severity=severity,
                    description=description,
                    detection=det,
                    thermal=thermal,
                    location=location,
                    timestamp=datetime.now(),
                    recommendations=recommendations,
                )
                anomalies.append(anomaly)

        # Thermal-based anomalies
        if thermal:
            for hx, hy in thermal.hotspot_locations:
                # Check if covered by existing anomaly
                is_covered = any(
                    a.detection.bbox.x1 <= hx <= a.detection.bbox.x2 and
                    a.detection.bbox.y1 <= hy <= a.detection.bbox.y2
                    for a in anomalies
                )

                if not is_covered:
                    # Find nearest detection
                    nearest_det = None
                    min_dist = float("inf")

                    for det in detections:
                        cx, cy = det.bbox.center
                        dist = ((cx - hx) ** 2 + (cy - hy) ** 2) ** 0.5
                        if dist < min_dist:
                            min_dist = dist
                            nearest_det = det

                    if nearest_det and min_dist < 100:
                        severity = self._thermal_severity(thermal)

                        anomaly = Anomaly(
                            id=str(uuid.uuid4())[:8],
                            type="thermal_anomaly",
                            severity=severity,
                            description=f"Thermal hotspot detected near {nearest_det.class_name}. "
                                       f"Max temperature: {thermal.max_temp:.1f}°C",
                            detection=nearest_det,
                            thermal=thermal,
                            location=location,
                            timestamp=datetime.now(),
                            recommendations=[
                                "Verify temperature readings with handheld thermal camera",
                                "Check for loose connections or internal faults",
                                "Schedule maintenance based on temperature trend",
                            ],
                        )
                        anomalies.append(anomaly)

        return anomalies

    def _assess_severity(
        self,
        detection: Detection,
        thermal: Optional[ThermalReading],
    ) -> SeverityLevel:
        """Assess severity based on detection and thermal data."""
        base_severity = {
            "damage": SeverityLevel.HIGH,
            "crack": SeverityLevel.HIGH,
            "leak": SeverityLevel.HIGH,
            "corrosion": SeverityLevel.MEDIUM,
            "hotspot": SeverityLevel.MEDIUM,
            "contamination": SeverityLevel.LOW,
        }.get(detection.class_name, SeverityLevel.INFO)

        # Adjust based on thermal
        if thermal:
            thermal_severity = self._thermal_severity(thermal)
            if thermal_severity.value > base_severity.value:
                return thermal_severity

        # Adjust based on confidence
        if detection.confidence > 0.9 and base_severity.value < SeverityLevel.HIGH.value:
            return SeverityLevel(base_severity.value + 1)

        return base_severity

    def _thermal_severity(self, thermal: ThermalReading) -> SeverityLevel:
        """Assess severity from thermal data."""
        if thermal.max_temp > 100 or thermal.delta_t > 50:
            return SeverityLevel.CRITICAL
        elif thermal.max_temp > 80 or thermal.delta_t > 30:
            return SeverityLevel.HIGH
        elif thermal.max_temp > 60 or thermal.delta_t > 15:
            return SeverityLevel.MEDIUM
        elif thermal.max_temp > 45 or thermal.delta_t > 10:
            return SeverityLevel.LOW
        return SeverityLevel.INFO

    def _get_default_recommendations(self, defect_type: str) -> list[str]:
        """Get default recommendations for defect types."""
        recommendations = {
            "damage": [
                "Assess structural integrity",
                "Schedule immediate inspection",
                "Document with high-resolution imagery",
            ],
            "corrosion": [
                "Evaluate extent of corrosion",
                "Check for protective coating degradation",
                "Schedule cleaning and treatment",
            ],
            "hotspot": [
                "Verify with thermal imaging",
                "Check electrical connections",
                "Monitor temperature trend",
            ],
            "leak": [
                "Identify leak source",
                "Check for environmental contamination",
                "Schedule repair",
            ],
            "crack": [
                "Measure crack dimensions",
                "Assess structural impact",
                "Schedule repair or replacement",
            ],
            "contamination": [
                "Identify contamination source",
                "Schedule cleaning",
                "Implement preventive measures",
            ],
        }

        return recommendations.get(defect_type, [
            "Document finding",
            "Schedule follow-up inspection",
        ])

    def _update_metrics(
        self,
        timing: dict,
        num_detections: int,
        num_anomalies: int,
    ) -> None:
        """Update pipeline metrics."""
        self._timing_history.append(timing)
        if len(self._timing_history) > 100:
            self._timing_history.pop(0)

        # Calculate averages
        self._metrics.total_frames += 1
        self._metrics.total_detections += num_detections
        self._metrics.total_anomalies += num_anomalies

        if self._timing_history:
            self._metrics.avg_yolo_time = np.mean([t.get("yolo", 0) for t in self._timing_history])
            self._metrics.avg_rfdetr_time = np.mean([t.get("rf_detr", 0) for t in self._timing_history])
            self._metrics.avg_sam3_time = np.mean([t.get("sam3", 0) for t in self._timing_history])
            self._metrics.avg_qwen_time = np.mean([t.get("qwen_vl", 0) for t in self._timing_history])
            self._metrics.avg_total_time = np.mean([t.get("total", 0) for t in self._timing_history])

        # Calculate FPS
        current_time = time.time()
        elapsed = current_time - self._last_time
        if elapsed > 0:
            instant_fps = 1.0 / elapsed
            self._fps_history.append(instant_fps)
            if len(self._fps_history) > 30:
                self._fps_history.pop(0)
            self._metrics.fps = np.mean(self._fps_history)
        self._last_time = current_time

    def get_metrics(self) -> PipelineMetrics:
        """Get current pipeline metrics."""
        return self._metrics

    async def shutdown(self) -> None:
        """Shutdown the pipeline and release resources."""
        logger.info("Shutting down inference pipeline...")

        if self.yolo:
            self.yolo.unload()
        if self.rf_detr:
            self.rf_detr.unload()
        if self.sam3:
            self.sam3.unload()
        if self.qwen_vl:
            self.qwen_vl.unload()

        self._executor.shutdown(wait=True)
        logger.info("Pipeline shutdown complete")
