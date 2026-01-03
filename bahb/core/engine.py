"""Main inspection engine orchestrating all BAHB components."""

from __future__ import annotations

import asyncio
import signal
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np
from numpy.typing import NDArray
from loguru import logger

from bahb.core.config import Config, load_config
from bahb.core.types import (
    Anomaly,
    CameraType,
    Detection,
    FrameData,
    GeoLocation,
    InspectionResult,
    InspectionSession,
    InspectionType,
    SeverityLevel,
    ThermalReading,
)
from bahb.camera.h30t import H30TCamera
from bahb.camera.frame_sync import FrameSynchronizer
from bahb.models.pipeline import InferencePipeline, PipelineMetrics
from bahb.thermal.analyzer import ThermalAnalyzer
from bahb.reporting.generator import ReportGenerator


class InspectionEngine:
    """
    Main orchestration engine for BAHB drone inspection system.

    This class coordinates:
    - Camera input from DJI H30T
    - AI inference pipeline
    - Thermal analysis
    - Anomaly detection
    - Report generation
    - Real-time streaming
    - Alert management
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or load_config()
        self.config.ensure_directories()

        # Core components
        self.camera: Optional[H30TCamera] = None
        self.pipeline: Optional[InferencePipeline] = None
        self.thermal_analyzer: Optional[ThermalAnalyzer] = None
        self.report_generator: Optional[ReportGenerator] = None
        self.frame_sync: Optional[FrameSynchronizer] = None

        # Session management
        self.session: Optional[InspectionSession] = None
        self._results: list[InspectionResult] = []

        # State
        self._running = False
        self._paused = False
        self._frame_count = 0

        # Callbacks
        self._on_detection: Optional[Callable[[list[Detection]], None]] = None
        self._on_anomaly: Optional[Callable[[Anomaly], None]] = None
        self._on_result: Optional[Callable[[InspectionResult], None]] = None
        self._on_frame: Optional[Callable[[FrameData], None]] = None

        # Statistics
        self._start_time: Optional[datetime] = None
        self._anomaly_counts = {level: 0 for level in SeverityLevel}

    async def initialize(self) -> bool:
        """Initialize all engine components."""
        logger.info("Initializing BAHB Inspection Engine...")

        try:
            # Initialize camera
            logger.info("Initializing H30T camera...")
            self.camera = H30TCamera(self.config.camera)
            self.camera.set_frame_callback(self._on_camera_frame)

            # Initialize frame synchronizer
            self.frame_sync = FrameSynchronizer(
                sync_tolerance_ms=50,
                alignment_enabled=True,
            )

            # Initialize AI pipeline
            logger.info("Initializing AI inference pipeline...")
            self.pipeline = InferencePipeline(self.config)

            if not await self.pipeline.initialize():
                logger.error("Failed to initialize AI pipeline")
                return False

            # Set pipeline callbacks
            self.pipeline.set_callbacks(
                on_detection=self._handle_detections,
                on_anomaly=self._handle_anomaly,
                on_result=self._handle_result,
            )

            # Initialize thermal analyzer
            if self.config.thermal.enabled:
                logger.info("Initializing thermal analyzer...")
                self.thermal_analyzer = ThermalAnalyzer(self.config.thermal)

            # Initialize report generator
            self.report_generator = ReportGenerator(
                output_dir=self.config.data_dir / "reports"
            )

            logger.info("BAHB Inspection Engine initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Engine initialization failed: {e}")
            return False

    async def start_inspection(
        self,
        inspection_type: InspectionType = InspectionType.SUBSTATION,
        site_name: str = "",
        pilot_id: str = "",
    ) -> str:
        """
        Start a new inspection session.

        Args:
            inspection_type: Type of infrastructure being inspected
            site_name: Name of the inspection site
            pilot_id: Operator identifier

        Returns:
            Session ID
        """
        # Create session
        session_id = str(uuid.uuid4())[:8]
        self.session = InspectionSession(
            session_id=session_id,
            inspection_type=inspection_type,
            start_time=datetime.now(),
            site_name=site_name,
            pilot_id=pilot_id,
            aircraft_serial=self.config.name,
        )

        self._results = []
        self._frame_count = 0
        self._start_time = datetime.now()
        self._anomaly_counts = {level: 0 for level in SeverityLevel}

        logger.info(f"Starting inspection session: {session_id}")
        logger.info(f"Type: {inspection_type.name}, Site: {site_name}")

        # Start camera
        await self.camera.start()

        # Start processing loop
        self._running = True
        asyncio.create_task(self._processing_loop())

        return session_id

    async def stop_inspection(self, generate_report: bool = True) -> Optional[Path]:
        """
        Stop current inspection session.

        Args:
            generate_report: Whether to generate final report

        Returns:
            Path to generated report, if any
        """
        self._running = False

        if self.camera:
            await self.camera.stop()

        if self.session:
            self.session.end_time = datetime.now()
            self.session.total_frames = self._frame_count
            self.session.total_detections = sum(len(r.detections) for r in self._results)
            self.session.total_anomalies = sum(len(r.anomalies) for r in self._results)
            self.session.critical_count = self._anomaly_counts[SeverityLevel.CRITICAL]
            self.session.high_count = self._anomaly_counts[SeverityLevel.HIGH]
            self.session.medium_count = self._anomaly_counts[SeverityLevel.MEDIUM]
            self.session.low_count = self._anomaly_counts[SeverityLevel.LOW]

            logger.info(f"Inspection session {self.session.session_id} complete")
            logger.info(f"Total frames: {self.session.total_frames}")
            logger.info(f"Total anomalies: {self.session.total_anomalies}")

            # Generate report
            if generate_report and self._results:
                report_path = self.report_generator.generate(
                    self.session,
                    self._results,
                    format="html",
                )
                self.session.report_path = str(report_path)
                return report_path

        return None

    def pause(self) -> None:
        """Pause inspection processing."""
        self._paused = True
        logger.info("Inspection paused")

    def resume(self) -> None:
        """Resume inspection processing."""
        self._paused = False
        logger.info("Inspection resumed")

    async def _processing_loop(self) -> None:
        """Main processing loop."""
        logger.info("Processing loop started")

        while self._running:
            if self._paused:
                await asyncio.sleep(0.1)
                continue

            try:
                # Get synchronized frame
                frame_data = await self._get_next_frame()
                if frame_data is None:
                    await asyncio.sleep(0.01)
                    continue

                self._frame_count += 1

                # Analyze thermal data if available
                thermal_reading = None
                if (
                    self.thermal_analyzer
                    and frame_data.thermal_raw is not None
                ):
                    thermal_reading = self.thermal_analyzer.analyze(
                        frame_data.thermal_raw
                    )

                # Process through AI pipeline
                result = await self.pipeline.process_frame(
                    frame_data,
                    thermal_reading,
                )

                # Store result
                self._results.append(result)

                # Update anomaly counts
                for anomaly in result.anomalies:
                    self._anomaly_counts[anomaly.severity] += 1

                # Limit stored results
                if len(self._results) > 1000:
                    self._results.pop(0)

            except Exception as e:
                logger.error(f"Processing error: {e}")
                await asyncio.sleep(0.1)

        logger.info("Processing loop stopped")

    async def _get_next_frame(self) -> Optional[FrameData]:
        """Get next synchronized frame from camera."""
        if self.camera is None:
            return None

        # Camera provides synchronized frames via callback
        # Here we could also implement frame buffering/queue
        return await self._wait_for_frame()

    async def _wait_for_frame(self, timeout: float = 0.1) -> Optional[FrameData]:
        """Wait for next frame with timeout."""
        # Simplified - actual implementation would use asyncio.Queue
        await asyncio.sleep(1.0 / 30)  # Target 30 FPS
        return None

    def _on_camera_frame(self, frame_data: FrameData) -> None:
        """Callback for camera frames."""
        if self._on_frame:
            self._on_frame(frame_data)

    def _handle_detections(self, detections: list[Detection]) -> None:
        """Handle detection events."""
        if self._on_detection:
            self._on_detection(detections)

    def _handle_anomaly(self, anomaly: Anomaly) -> None:
        """Handle anomaly events."""
        logger.warning(
            f"Anomaly detected: {anomaly.type} [{anomaly.severity.name}] - {anomaly.description}"
        )

        if self._on_anomaly:
            self._on_anomaly(anomaly)

        # Auto-alert for critical anomalies
        if anomaly.severity == SeverityLevel.CRITICAL:
            self._send_alert(anomaly)

    def _handle_result(self, result: InspectionResult) -> None:
        """Handle inspection result events."""
        if self._on_result:
            self._on_result(result)

    def _send_alert(self, anomaly: Anomaly) -> None:
        """Send alert for critical anomaly."""
        logger.critical(f"ALERT: {anomaly.description}")
        # TODO: Implement MQTT/webhook alerts

    def set_callbacks(
        self,
        on_detection: Optional[Callable[[list[Detection]], None]] = None,
        on_anomaly: Optional[Callable[[Anomaly], None]] = None,
        on_result: Optional[Callable[[InspectionResult], None]] = None,
        on_frame: Optional[Callable[[FrameData], None]] = None,
    ) -> None:
        """Set event callbacks."""
        self._on_detection = on_detection
        self._on_anomaly = on_anomaly
        self._on_result = on_result
        self._on_frame = on_frame

    def get_metrics(self) -> dict:
        """Get current engine metrics."""
        pipeline_metrics = self.pipeline.get_metrics() if self.pipeline else PipelineMetrics()

        return {
            "session_id": self.session.session_id if self.session else None,
            "running": self._running,
            "paused": self._paused,
            "frame_count": self._frame_count,
            "result_count": len(self._results),
            "anomaly_counts": {k.name: v for k, v in self._anomaly_counts.items()},
            "pipeline": {
                "total_frames": pipeline_metrics.total_frames,
                "total_detections": pipeline_metrics.total_detections,
                "fps": pipeline_metrics.fps,
                "avg_inference_ms": pipeline_metrics.avg_total_time,
            },
            "uptime_seconds": (
                (datetime.now() - self._start_time).total_seconds()
                if self._start_time else 0
            ),
        }

    async def process_single_image(
        self,
        image: NDArray,
        thermal_image: Optional[NDArray] = None,
        location: Optional[GeoLocation] = None,
    ) -> InspectionResult:
        """
        Process a single image for inspection.

        Useful for batch processing or testing.

        Args:
            image: RGB/BGR image
            thermal_image: Optional thermal image
            location: Optional GPS location

        Returns:
            InspectionResult
        """
        # Create frame data
        frame_data = FrameData(
            timestamp=datetime.now(),
            frame_id=0,
            wide_image=image,
            thermal_image=thermal_image,
            location=location,
        )

        # Analyze thermal
        thermal_reading = None
        if self.thermal_analyzer and thermal_image is not None:
            if thermal_image.dtype == np.uint8:
                thermal_reading = self.thermal_analyzer.analyze(thermal_image)
            else:
                thermal_reading = self.thermal_analyzer.analyze(thermal_image)

        # Process through pipeline
        result = await self.pipeline.process_frame(frame_data, thermal_reading)

        return result

    async def shutdown(self) -> None:
        """Shutdown engine and release all resources."""
        logger.info("Shutting down BAHB Inspection Engine...")

        self._running = False

        if self.camera:
            await self.camera.stop()

        if self.pipeline:
            await self.pipeline.shutdown()

        logger.info("Engine shutdown complete")


async def run_inspection(
    config_path: Optional[str] = None,
    inspection_type: str = "substation",
    site_name: str = "Unknown Site",
    duration_seconds: Optional[int] = None,
) -> None:
    """
    Run a complete inspection session.

    Args:
        config_path: Path to configuration file
        inspection_type: Type of inspection (substation, datacenter)
        site_name: Name of the site
        duration_seconds: Optional duration limit
    """
    # Load config
    config = load_config(config_path)

    # Create engine
    engine = InspectionEngine(config)

    # Setup signal handlers
    loop = asyncio.get_event_loop()

    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(engine.stop_inspection())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        # Initialize
        if not await engine.initialize():
            logger.error("Engine initialization failed")
            return

        # Map inspection type
        type_map = {
            "substation": InspectionType.SUBSTATION,
            "datacenter": InspectionType.DATACENTER,
        }
        insp_type = type_map.get(inspection_type.lower(), InspectionType.SUBSTATION)

        # Start inspection
        session_id = await engine.start_inspection(
            inspection_type=insp_type,
            site_name=site_name,
        )

        logger.info(f"Inspection started: {session_id}")

        # Run for duration or until stopped
        if duration_seconds:
            await asyncio.sleep(duration_seconds)
            report_path = await engine.stop_inspection()
            logger.info(f"Report generated: {report_path}")
        else:
            # Run indefinitely
            while engine._running:
                await asyncio.sleep(1)
                metrics = engine.get_metrics()
                logger.info(
                    f"Frames: {metrics['frame_count']} | "
                    f"Anomalies: {sum(metrics['anomaly_counts'].values())} | "
                    f"FPS: {metrics['pipeline']['fps']:.1f}"
                )

    finally:
        await engine.shutdown()
