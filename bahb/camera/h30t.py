"""DJI H30T multi-sensor camera interface."""

from __future__ import annotations

import asyncio
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Optional

import cv2
import numpy as np
from numpy.typing import NDArray
from loguru import logger

from bahb.core.config import H30TConfig
from bahb.core.types import CameraType, FrameData, GeoLocation


class StreamState(Enum):
    """Camera stream state."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    ERROR = "error"


@dataclass
class StreamStats:
    """Stream statistics."""
    frames_received: int = 0
    frames_dropped: int = 0
    last_frame_time: float = 0.0
    avg_fps: float = 0.0
    bitrate_kbps: float = 0.0
    latency_ms: float = 0.0


class CameraStream:
    """Individual camera stream handler."""

    def __init__(
        self,
        stream_type: CameraType,
        rtsp_url: str,
        resolution: tuple[int, int] = (1920, 1080),
        fps: int = 30,
        buffer_size: int = 5,
    ):
        self.stream_type = stream_type
        self.rtsp_url = rtsp_url
        self.resolution = resolution
        self.target_fps = fps
        self.buffer_size = buffer_size

        self._capture: Optional[cv2.VideoCapture] = None
        self._state = StreamState.DISCONNECTED
        self._frame_buffer: deque = deque(maxlen=buffer_size)
        self._stats = StreamStats()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Callbacks
        self._on_frame: Optional[Callable[[NDArray, datetime], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None

    @property
    def state(self) -> StreamState:
        return self._state

    @property
    def stats(self) -> StreamStats:
        return self._stats

    def set_callbacks(
        self,
        on_frame: Optional[Callable[[NDArray, datetime], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """Set callback functions."""
        self._on_frame = on_frame
        self._on_error = on_error

    def connect(self) -> bool:
        """Connect to RTSP stream."""
        self._state = StreamState.CONNECTING
        logger.info(f"Connecting to {self.stream_type.value} stream: {self.rtsp_url}")

        try:
            # Configure GStreamer pipeline for low-latency
            gst_pipeline = self._build_gstreamer_pipeline()

            self._capture = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

            if not self._capture.isOpened():
                # Fallback to FFmpeg
                logger.warning("GStreamer failed, falling back to FFmpeg")
                self._capture = cv2.VideoCapture(self.rtsp_url)

                if not self._capture.isOpened():
                    raise ConnectionError(f"Failed to open stream: {self.rtsp_url}")

            # Set buffer size for low latency
            self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            self._state = StreamState.CONNECTED
            logger.info(f"{self.stream_type.value} stream connected")
            return True

        except Exception as e:
            self._state = StreamState.ERROR
            logger.error(f"Failed to connect: {e}")
            if self._on_error:
                self._on_error(e)
            return False

    def _build_gstreamer_pipeline(self) -> str:
        """Build GStreamer pipeline for H30T RTSP stream."""
        # Optimized for NVIDIA Jetson/Orin hardware decoding
        pipeline = (
            f"rtspsrc location={self.rtsp_url} latency=50 ! "
            "rtph265depay ! h265parse ! "
            "nvv4l2decoder ! "
            "nvvidconv ! "
            f"video/x-raw, width={self.resolution[0]}, height={self.resolution[1]}, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! "
            "appsink drop=1 max-buffers=1"
        )
        return pipeline

    def start(self) -> None:
        """Start frame capture thread."""
        if self._running:
            return

        if self._state != StreamState.CONNECTED:
            if not self.connect():
                return

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        self._state = StreamState.STREAMING
        logger.info(f"{self.stream_type.value} stream started")

    def stop(self) -> None:
        """Stop frame capture."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._capture:
            self._capture.release()
            self._capture = None
        self._state = StreamState.DISCONNECTED
        logger.info(f"{self.stream_type.value} stream stopped")

    def _capture_loop(self) -> None:
        """Main capture loop running in separate thread."""
        frame_count = 0
        start_time = time.time()
        last_fps_update = start_time

        while self._running:
            try:
                ret, frame = self._capture.read()

                if not ret:
                    self._stats.frames_dropped += 1
                    logger.warning(f"{self.stream_type.value}: Frame drop")
                    time.sleep(0.01)
                    continue

                timestamp = datetime.now()
                frame_count += 1
                self._stats.frames_received += 1
                self._stats.last_frame_time = time.time()

                # Update FPS calculation
                current_time = time.time()
                if current_time - last_fps_update >= 1.0:
                    self._stats.avg_fps = frame_count / (current_time - last_fps_update)
                    frame_count = 0
                    last_fps_update = current_time

                # Store in buffer
                with self._lock:
                    self._frame_buffer.append((frame, timestamp))

                # Callback
                if self._on_frame:
                    self._on_frame(frame, timestamp)

            except Exception as e:
                logger.error(f"Capture error: {e}")
                if self._on_error:
                    self._on_error(e)
                time.sleep(0.1)

    def get_latest_frame(self) -> Optional[tuple[NDArray, datetime]]:
        """Get the most recent frame."""
        with self._lock:
            if self._frame_buffer:
                return self._frame_buffer[-1]
        return None

    def get_frame(self, timeout: float = 1.0) -> Optional[tuple[NDArray, datetime]]:
        """Get frame from buffer with timeout."""
        start = time.time()
        while time.time() - start < timeout:
            with self._lock:
                if self._frame_buffer:
                    return self._frame_buffer.popleft()
            time.sleep(0.01)
        return None


class H30TCamera:
    """DJI H30T multi-sensor camera controller."""

    def __init__(self, config: H30TConfig):
        self.config = config

        # Initialize camera streams
        self.streams: dict[CameraType, CameraStream] = {}

        if config.wide.enabled:
            self.streams[CameraType.WIDE] = CameraStream(
                stream_type=CameraType.WIDE,
                rtsp_url=config.streams.get("wide", ""),
                resolution=tuple(config.wide.resolution),
                fps=config.wide.fps,
            )

        if config.zoom.enabled:
            self.streams[CameraType.ZOOM] = CameraStream(
                stream_type=CameraType.ZOOM,
                rtsp_url=config.streams.get("zoom", ""),
                resolution=tuple(config.zoom.resolution),
                fps=config.zoom.fps,
            )

        if config.thermal.enabled:
            self.streams[CameraType.THERMAL] = CameraStream(
                stream_type=CameraType.THERMAL,
                rtsp_url=config.streams.get("thermal", ""),
                resolution=tuple(config.thermal.resolution),
                fps=config.thermal.fps,
            )

        # Gimbal and telemetry
        self._gimbal_attitude: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._zoom_level: float = 1.0
        self._laser_distance: Optional[float] = None
        self._location: Optional[GeoLocation] = None

        # Frame sync
        self._frame_id = 0
        self._sync_tolerance_ms = 50  # Max time diff for synchronized frames

        # Callbacks
        self._on_frame_sync: Optional[Callable[[FrameData], None]] = None

        logger.info("H30T camera initialized")

    def set_frame_callback(self, callback: Callable[[FrameData], None]) -> None:
        """Set callback for synchronized frame data."""
        self._on_frame_sync = callback

    async def start(self) -> None:
        """Start all camera streams."""
        logger.info("Starting H30T camera streams")

        for camera_type, stream in self.streams.items():
            stream.start()

        # Start frame synchronization task
        asyncio.create_task(self._frame_sync_loop())

    async def stop(self) -> None:
        """Stop all camera streams."""
        for stream in self.streams.values():
            stream.stop()
        logger.info("H30T camera stopped")

    async def _frame_sync_loop(self) -> None:
        """Synchronize frames from all camera streams."""
        while True:
            try:
                frame_data = await self._get_synchronized_frame()
                if frame_data and self._on_frame_sync:
                    self._on_frame_sync(frame_data)
            except Exception as e:
                logger.error(f"Frame sync error: {e}")

            await asyncio.sleep(1.0 / 30)  # Target 30 FPS synchronized output

    async def _get_synchronized_frame(self) -> Optional[FrameData]:
        """Get synchronized frames from all cameras."""
        frames: dict[CameraType, tuple[NDArray, datetime]] = {}

        reference_time = None
        for camera_type, stream in self.streams.items():
            result = stream.get_latest_frame()
            if result:
                frame, timestamp = result
                if reference_time is None:
                    reference_time = timestamp

                # Check sync tolerance
                time_diff = abs((timestamp - reference_time).total_seconds() * 1000)
                if time_diff <= self._sync_tolerance_ms:
                    frames[camera_type] = (frame, timestamp)

        if not frames:
            return None

        self._frame_id += 1

        frame_data = FrameData(
            timestamp=reference_time or datetime.now(),
            frame_id=self._frame_id,
            location=self._location,
            gimbal_attitude=self._gimbal_attitude,
            zoom_level=self._zoom_level,
            laser_distance=self._laser_distance,
        )

        if CameraType.WIDE in frames:
            frame_data.wide_image = frames[CameraType.WIDE][0]

        if CameraType.ZOOM in frames:
            frame_data.zoom_image = frames[CameraType.ZOOM][0]

        if CameraType.THERMAL in frames:
            thermal_frame = frames[CameraType.THERMAL][0]
            frame_data.thermal_image = thermal_frame
            # Convert to raw temperatures if needed
            frame_data.thermal_raw = self._decode_thermal_raw(thermal_frame)

        return frame_data

    def _decode_thermal_raw(self, thermal_frame: NDArray) -> NDArray[np.float32]:
        """Decode thermal frame to raw temperature values."""
        # H30T thermal stream provides radiometric data
        # Convert from 14-bit raw to temperature in Celsius
        # This is a simplified conversion - actual H30T uses proprietary format

        if len(thermal_frame.shape) == 3:
            # Convert color to grayscale intensity
            gray = cv2.cvtColor(thermal_frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = thermal_frame

        # Map to temperature range (simplified linear mapping)
        # In production, use DJI SDK for accurate radiometric data
        temp_min, temp_max = self.config.thermal.temperature_range
        normalized = gray.astype(np.float32) / 255.0
        temperatures = normalized * (temp_max - temp_min) + temp_min

        return temperatures

    def set_zoom(self, zoom_level: float) -> None:
        """Set optical zoom level (5x - 200x)."""
        zoom_level = max(5.0, min(200.0, zoom_level))
        self._zoom_level = zoom_level
        logger.debug(f"Zoom set to: {zoom_level}x")

    def set_thermal_palette(self, palette: str) -> None:
        """Set thermal color palette."""
        valid_palettes = ["white_hot", "black_hot", "ironbow", "rainbow", "lava"]
        if palette not in valid_palettes:
            logger.warning(f"Invalid palette: {palette}")
            return
        logger.debug(f"Thermal palette: {palette}")

    def update_telemetry(
        self,
        location: Optional[GeoLocation] = None,
        gimbal: Optional[tuple[float, float, float]] = None,
        laser_distance: Optional[float] = None,
    ) -> None:
        """Update telemetry data."""
        if location:
            self._location = location
        if gimbal:
            self._gimbal_attitude = gimbal
        if laser_distance is not None:
            self._laser_distance = laser_distance

    def capture_still(self, camera: CameraType = CameraType.WIDE) -> Optional[NDArray]:
        """Capture a still image from specified camera."""
        if camera not in self.streams:
            return None

        result = self.streams[camera].get_latest_frame()
        if result:
            return result[0].copy()
        return None

    def get_stream_stats(self) -> dict[str, StreamStats]:
        """Get statistics for all streams."""
        return {
            camera_type.value: stream.stats
            for camera_type, stream in self.streams.items()
        }
