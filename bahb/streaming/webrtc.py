"""WebRTC streaming for real-time inspection visualization."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Callable, Optional

import cv2
import numpy as np
from numpy.typing import NDArray
from loguru import logger

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
    from aiortc.contrib.media import MediaRelay
    from av import VideoFrame
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    logger.warning("aiortc not available, WebRTC streaming disabled")


@dataclass
class StreamConfig:
    """WebRTC stream configuration."""
    port: int = 8080
    stun_servers: list[str] = None
    video_bitrate: int = 2000000  # 2 Mbps
    framerate: int = 30
    resolution: tuple[int, int] = (1280, 720)


class AnnotatedVideoTrack:
    """Video track that overlays detection results on frames."""

    def __init__(
        self,
        resolution: tuple[int, int] = (1280, 720),
        framerate: int = 30,
    ):
        self.resolution = resolution
        self.framerate = framerate
        self._frame: Optional[NDArray] = None
        self._detections: list = []
        self._anomalies: list = []
        self._thermal_overlay: Optional[NDArray] = None
        self._show_detections = True
        self._show_thermal = False
        self._show_stats = True
        self._stats: dict = {}

    def update_frame(
        self,
        frame: NDArray,
        detections: list = None,
        anomalies: list = None,
        thermal_overlay: NDArray = None,
        stats: dict = None,
    ) -> None:
        """Update the current frame and overlays."""
        self._frame = frame
        if detections is not None:
            self._detections = detections
        if anomalies is not None:
            self._anomalies = anomalies
        if thermal_overlay is not None:
            self._thermal_overlay = thermal_overlay
        if stats is not None:
            self._stats = stats

    def get_annotated_frame(self) -> Optional[NDArray]:
        """Get frame with all overlays applied."""
        if self._frame is None:
            return None

        frame = self._frame.copy()

        # Resize if needed
        if frame.shape[:2] != self.resolution[::-1]:
            frame = cv2.resize(frame, self.resolution)

        # Apply thermal overlay
        if self._show_thermal and self._thermal_overlay is not None:
            thermal = cv2.resize(self._thermal_overlay, self.resolution)
            frame = cv2.addWeighted(frame, 0.6, thermal, 0.4, 0)

        # Draw detections
        if self._show_detections:
            frame = self._draw_detections(frame)

        # Draw anomaly markers
        frame = self._draw_anomalies(frame)

        # Draw statistics overlay
        if self._show_stats:
            frame = self._draw_stats(frame)

        return frame

    def _draw_detections(self, frame: NDArray) -> NDArray:
        """Draw detection bounding boxes."""
        for det in self._detections:
            bbox = det.bbox
            x1, y1 = int(bbox.x1), int(bbox.y1)
            x2, y2 = int(bbox.x2), int(bbox.y2)

            # Scale to current resolution
            h, w = frame.shape[:2]
            scale_x = w / 1920 if hasattr(bbox, '_orig_w') else 1
            scale_y = h / 1080 if hasattr(bbox, '_orig_h') else 1

            x1, x2 = int(x1 * scale_x), int(x2 * scale_x)
            y1, y2 = int(y1 * scale_y), int(y2 * scale_y)

            # Color based on class
            color = self._get_class_color(det.class_name)

            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Draw label
            label = f"{det.class_name} {det.confidence:.0%}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]

            cv2.rectangle(
                frame,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0] + 10, y1),
                color,
                -1,
            )
            cv2.putText(
                frame,
                label,
                (x1 + 5, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

        return frame

    def _draw_anomalies(self, frame: NDArray) -> NDArray:
        """Draw anomaly warning markers."""
        for anomaly in self._anomalies:
            bbox = anomaly.detection.bbox
            cx, cy = int(bbox.center[0]), int(bbox.center[1])

            # Severity-based color
            severity_colors = {
                "CRITICAL": (0, 0, 255),
                "HIGH": (0, 128, 255),
                "MEDIUM": (0, 255, 255),
                "LOW": (0, 255, 0),
                "INFO": (255, 255, 0),
            }
            color = severity_colors.get(anomaly.severity.name, (128, 128, 128))

            # Pulsing circle effect
            radius = 30 + int(10 * np.sin(time.time() * 5))
            cv2.circle(frame, (cx, cy), radius, color, 3)
            cv2.circle(frame, (cx, cy), radius - 10, color, 2)

            # Warning icon
            cv2.putText(
                frame,
                "!",
                (cx - 8, cy + 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                color,
                3,
            )

        return frame

    def _draw_stats(self, frame: NDArray) -> NDArray:
        """Draw statistics overlay."""
        h, w = frame.shape[:2]

        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (250, 120), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)

        # Stats text
        stats_lines = [
            f"FPS: {self._stats.get('fps', 0):.1f}",
            f"Detections: {len(self._detections)}",
            f"Anomalies: {len(self._anomalies)}",
            f"Inference: {self._stats.get('inference_ms', 0):.1f}ms",
        ]

        y = 35
        for line in stats_lines:
            cv2.putText(
                frame,
                line,
                (20, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1,
            )
            y += 25

        # Timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            frame,
            timestamp,
            (w - 200, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        return frame

    def _get_class_color(self, class_name: str) -> tuple[int, int, int]:
        """Get color for detection class."""
        colors = {
            "transformer": (255, 128, 0),
            "insulator": (0, 255, 128),
            "conductor": (128, 255, 0),
            "switchgear": (255, 0, 128),
            "damage": (0, 0, 255),
            "corrosion": (0, 128, 255),
            "hotspot": (0, 0, 255),
            "leak": (255, 0, 0),
            "server_rack": (128, 128, 255),
            "hvac_unit": (128, 255, 128),
        }
        return colors.get(class_name, (0, 255, 0))

    def toggle_detections(self) -> None:
        """Toggle detection overlay."""
        self._show_detections = not self._show_detections

    def toggle_thermal(self) -> None:
        """Toggle thermal overlay."""
        self._show_thermal = not self._show_thermal

    def toggle_stats(self) -> None:
        """Toggle statistics overlay."""
        self._show_stats = not self._show_stats


class WebRTCStreamer:
    """
    WebRTC streamer for real-time inspection video.

    Provides low-latency streaming of annotated inspection video
    to web clients via WebRTC.
    """

    def __init__(self, config: StreamConfig = None):
        self.config = config or StreamConfig()
        self._track = AnnotatedVideoTrack(
            resolution=self.config.resolution,
            framerate=self.config.framerate,
        )
        self._peer_connections: set = set()
        self._running = False

    async def start(self) -> None:
        """Start WebRTC server."""
        if not WEBRTC_AVAILABLE:
            logger.warning("WebRTC not available")
            return

        self._running = True
        logger.info(f"WebRTC streamer started on port {self.config.port}")

    async def stop(self) -> None:
        """Stop WebRTC server."""
        self._running = False

        # Close all peer connections
        for pc in self._peer_connections:
            await pc.close()
        self._peer_connections.clear()

        logger.info("WebRTC streamer stopped")

    def update_frame(
        self,
        frame: NDArray,
        detections: list = None,
        anomalies: list = None,
        thermal_overlay: NDArray = None,
        stats: dict = None,
    ) -> None:
        """Update the video frame."""
        self._track.update_frame(
            frame=frame,
            detections=detections,
            anomalies=anomalies,
            thermal_overlay=thermal_overlay,
            stats=stats,
        )

    async def handle_offer(self, offer_sdp: str) -> str:
        """
        Handle WebRTC offer and return answer.

        This would be called from a signaling server endpoint.
        """
        if not WEBRTC_AVAILABLE:
            return json.dumps({"error": "WebRTC not available"})

        offer = RTCSessionDescription(sdp=offer_sdp, type="offer")

        pc = RTCPeerConnection()
        self._peer_connections.add(pc)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            if pc.connectionState == "failed":
                await pc.close()
                self._peer_connections.discard(pc)

        # Add video track
        # In a full implementation, create a proper VideoStreamTrack
        # pc.addTrack(self._create_video_track())

        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return json.dumps({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type,
        })

    def get_jpeg_frame(self, quality: int = 85) -> Optional[bytes]:
        """Get current frame as JPEG for MJPEG fallback."""
        frame = self._track.get_annotated_frame()
        if frame is None:
            return None

        _, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, quality],
        )
        return buffer.tobytes()


class VideoRecorder:
    """Record inspection video to file."""

    def __init__(
        self,
        output_path: str,
        resolution: tuple[int, int] = (1920, 1080),
        fps: int = 30,
        codec: str = "mp4v",
    ):
        self.output_path = output_path
        self.resolution = resolution
        self.fps = fps
        self.codec = codec

        self._writer: Optional[cv2.VideoWriter] = None
        self._frame_count = 0
        self._start_time: Optional[float] = None

    def start(self) -> None:
        """Start recording."""
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        self._writer = cv2.VideoWriter(
            self.output_path,
            fourcc,
            self.fps,
            self.resolution,
        )
        self._start_time = time.time()
        self._frame_count = 0
        logger.info(f"Recording started: {self.output_path}")

    def write_frame(self, frame: NDArray) -> None:
        """Write frame to video."""
        if self._writer is None:
            return

        if frame.shape[:2] != self.resolution[::-1]:
            frame = cv2.resize(frame, self.resolution)

        self._writer.write(frame)
        self._frame_count += 1

    def stop(self) -> dict:
        """Stop recording and return stats."""
        if self._writer:
            self._writer.release()
            self._writer = None

        duration = time.time() - self._start_time if self._start_time else 0

        stats = {
            "output_path": self.output_path,
            "frame_count": self._frame_count,
            "duration_seconds": duration,
            "actual_fps": self._frame_count / duration if duration > 0 else 0,
        }

        logger.info(f"Recording stopped: {self._frame_count} frames, {duration:.1f}s")
        return stats

    @property
    def is_recording(self) -> bool:
        return self._writer is not None
