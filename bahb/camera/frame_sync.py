"""Frame synchronization and alignment for multi-sensor data."""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

import cv2
import numpy as np
from numpy.typing import NDArray
from loguru import logger

from bahb.core.types import CameraType, FrameData


@dataclass
class CalibrationData:
    """Camera calibration and alignment data."""
    # Intrinsic matrices
    wide_matrix: NDArray[np.float64]
    thermal_matrix: NDArray[np.float64]
    zoom_matrix: NDArray[np.float64]

    # Distortion coefficients
    wide_distortion: NDArray[np.float64]
    thermal_distortion: NDArray[np.float64]
    zoom_distortion: NDArray[np.float64]

    # Extrinsic (relative transforms)
    thermal_to_wide_rotation: NDArray[np.float64]
    thermal_to_wide_translation: NDArray[np.float64]

    # Homography matrices for quick alignment
    thermal_to_wide_homography: NDArray[np.float64]


class FrameSynchronizer:
    """Synchronize and align frames from multiple camera streams."""

    def __init__(
        self,
        sync_tolerance_ms: float = 50.0,
        buffer_size: int = 10,
        alignment_enabled: bool = True,
    ):
        self.sync_tolerance_ms = sync_tolerance_ms
        self.buffer_size = buffer_size
        self.alignment_enabled = alignment_enabled

        # Frame buffers per camera
        self._buffers: dict[CameraType, deque] = {
            CameraType.WIDE: deque(maxlen=buffer_size),
            CameraType.ZOOM: deque(maxlen=buffer_size),
            CameraType.THERMAL: deque(maxlen=buffer_size),
        }

        # Calibration
        self._calibration: Optional[CalibrationData] = None
        self._load_default_calibration()

        # Output callback
        self._on_sync_frame: Optional[Callable[[FrameData], None]] = None

        # Statistics
        self._sync_count = 0
        self._miss_count = 0

    def _load_default_calibration(self) -> None:
        """Load default calibration for H30T camera array."""
        # Default calibration matrices (should be replaced with actual calibration)
        # These are approximate values for H30T sensor geometry

        # Wide camera (4096x2160, 82.9° DFOV)
        wide_fx = 2400.0
        wide_fy = 2400.0
        wide_cx = 2048.0
        wide_cy = 1080.0

        # Thermal camera (640x512, 40.6° FOV)
        thermal_fx = 750.0
        thermal_fy = 750.0
        thermal_cx = 320.0
        thermal_cy = 256.0

        self._calibration = CalibrationData(
            wide_matrix=np.array([
                [wide_fx, 0, wide_cx],
                [0, wide_fy, wide_cy],
                [0, 0, 1]
            ], dtype=np.float64),
            thermal_matrix=np.array([
                [thermal_fx, 0, thermal_cx],
                [0, thermal_fy, thermal_cy],
                [0, 0, 1]
            ], dtype=np.float64),
            zoom_matrix=np.eye(3, dtype=np.float64),  # Variable based on zoom
            wide_distortion=np.zeros(5, dtype=np.float64),
            thermal_distortion=np.zeros(5, dtype=np.float64),
            zoom_distortion=np.zeros(5, dtype=np.float64),
            thermal_to_wide_rotation=np.eye(3, dtype=np.float64),
            thermal_to_wide_translation=np.array([0.05, 0.0, 0.0], dtype=np.float64),
            thermal_to_wide_homography=np.eye(3, dtype=np.float64),
        )

    def load_calibration(self, calibration_file: str) -> None:
        """Load calibration from file."""
        try:
            fs = cv2.FileStorage(calibration_file, cv2.FILE_STORAGE_READ)
            if not fs.isOpened():
                logger.warning(f"Could not open calibration file: {calibration_file}")
                return

            self._calibration = CalibrationData(
                wide_matrix=fs.getNode("wide_matrix").mat(),
                thermal_matrix=fs.getNode("thermal_matrix").mat(),
                zoom_matrix=fs.getNode("zoom_matrix").mat(),
                wide_distortion=fs.getNode("wide_distortion").mat(),
                thermal_distortion=fs.getNode("thermal_distortion").mat(),
                zoom_distortion=fs.getNode("zoom_distortion").mat(),
                thermal_to_wide_rotation=fs.getNode("thermal_to_wide_R").mat(),
                thermal_to_wide_translation=fs.getNode("thermal_to_wide_T").mat(),
                thermal_to_wide_homography=fs.getNode("thermal_to_wide_H").mat(),
            )
            fs.release()
            logger.info("Calibration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load calibration: {e}")

    def set_callback(self, callback: Callable[[FrameData], None]) -> None:
        """Set synchronized frame callback."""
        self._on_sync_frame = callback

    def add_frame(
        self,
        camera_type: CameraType,
        frame: NDArray,
        timestamp: datetime,
        metadata: Optional[dict] = None,
    ) -> None:
        """Add frame to buffer for synchronization."""
        self._buffers[camera_type].append({
            "frame": frame,
            "timestamp": timestamp,
            "metadata": metadata or {},
        })

    def try_sync(self) -> Optional[FrameData]:
        """Attempt to synchronize frames from all cameras."""
        if not self._buffers[CameraType.WIDE]:
            return None

        # Use latest wide frame as reference
        reference = self._buffers[CameraType.WIDE][-1]
        ref_time = reference["timestamp"]

        frames = {CameraType.WIDE: reference}

        # Find matching frames within tolerance
        for camera_type in [CameraType.ZOOM, CameraType.THERMAL]:
            if not self._buffers[camera_type]:
                continue

            best_match = None
            best_diff = float("inf")

            for entry in self._buffers[camera_type]:
                diff = abs((entry["timestamp"] - ref_time).total_seconds() * 1000)
                if diff < best_diff and diff <= self.sync_tolerance_ms:
                    best_diff = diff
                    best_match = entry

            if best_match:
                frames[camera_type] = best_match

        # Create synchronized frame data
        frame_data = FrameData(
            timestamp=ref_time,
            frame_id=self._sync_count,
        )

        if CameraType.WIDE in frames:
            frame_data.wide_image = frames[CameraType.WIDE]["frame"]

        if CameraType.ZOOM in frames:
            frame_data.zoom_image = frames[CameraType.ZOOM]["frame"]

        if CameraType.THERMAL in frames:
            frame_data.thermal_image = frames[CameraType.THERMAL]["frame"]
            if self.alignment_enabled and frame_data.wide_image is not None:
                frame_data.thermal_image = self.align_thermal_to_wide(
                    frame_data.thermal_image,
                    frame_data.wide_image.shape[:2],
                )

        self._sync_count += 1

        if self._on_sync_frame:
            self._on_sync_frame(frame_data)

        return frame_data

    def align_thermal_to_wide(
        self,
        thermal_frame: NDArray,
        target_size: tuple[int, int],
    ) -> NDArray:
        """Align thermal image to wide camera view."""
        if self._calibration is None:
            # Simple resize if no calibration
            return cv2.resize(thermal_frame, (target_size[1], target_size[0]))

        # Apply homography transformation
        aligned = cv2.warpPerspective(
            thermal_frame,
            self._calibration.thermal_to_wide_homography,
            (target_size[1], target_size[0]),
            flags=cv2.INTER_LINEAR,
        )

        return aligned

    def project_thermal_point_to_wide(
        self,
        thermal_point: tuple[int, int],
    ) -> tuple[int, int]:
        """Project a point from thermal to wide camera coordinates."""
        if self._calibration is None:
            return thermal_point

        point = np.array([[[thermal_point[0], thermal_point[1]]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(
            point,
            self._calibration.thermal_to_wide_homography,
        )
        return (int(transformed[0, 0, 0]), int(transformed[0, 0, 1]))

    def project_wide_point_to_thermal(
        self,
        wide_point: tuple[int, int],
    ) -> tuple[int, int]:
        """Project a point from wide to thermal camera coordinates."""
        if self._calibration is None:
            return wide_point

        # Inverse homography
        H_inv = np.linalg.inv(self._calibration.thermal_to_wide_homography)
        point = np.array([[[wide_point[0], wide_point[1]]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, H_inv)
        return (int(transformed[0, 0, 0]), int(transformed[0, 0, 1]))

    def create_fusion_image(
        self,
        wide_image: NDArray,
        thermal_image: NDArray,
        alpha: float = 0.5,
    ) -> NDArray:
        """Create fused RGB + thermal overlay image."""
        # Align thermal to wide
        thermal_aligned = self.align_thermal_to_wide(
            thermal_image,
            wide_image.shape[:2],
        )

        # Ensure thermal is 3-channel
        if len(thermal_aligned.shape) == 2:
            thermal_colored = cv2.applyColorMap(
                thermal_aligned.astype(np.uint8),
                cv2.COLORMAP_INFERNO,
            )
        else:
            thermal_colored = thermal_aligned

        # Blend images
        fused = cv2.addWeighted(wide_image, 1 - alpha, thermal_colored, alpha, 0)
        return fused

    def get_statistics(self) -> dict:
        """Get synchronization statistics."""
        return {
            "sync_count": self._sync_count,
            "miss_count": self._miss_count,
            "sync_rate": (
                self._sync_count / (self._sync_count + self._miss_count)
                if (self._sync_count + self._miss_count) > 0
                else 0.0
            ),
            "buffer_sizes": {
                camera_type.value: len(buffer)
                for camera_type, buffer in self._buffers.items()
            },
        }
