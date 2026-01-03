"""Core type definitions for BAHB inspection system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional
import numpy as np
from numpy.typing import NDArray


class SeverityLevel(Enum):
    """Anomaly severity classification."""
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class InspectionType(Enum):
    """Type of infrastructure being inspected."""
    SUBSTATION = auto()
    DATACENTER = auto()
    TRANSMISSION_LINE = auto()
    SOLAR_FARM = auto()
    WIND_TURBINE = auto()


class CameraType(Enum):
    """H30T camera types."""
    WIDE = "wide"
    ZOOM = "zoom"
    THERMAL = "thermal"


class DetectionClass(Enum):
    """Object detection classes for infrastructure inspection."""
    # Substation components
    TRANSFORMER = "transformer"
    INSULATOR = "insulator"
    CONDUCTOR = "conductor"
    SWITCHGEAR = "switchgear"
    CIRCUIT_BREAKER = "circuit_breaker"
    DISCONNECT_SWITCH = "disconnect_switch"
    CAPACITOR_BANK = "capacitor_bank"
    LIGHTNING_ARRESTER = "lightning_arrester"

    # Data center components
    SERVER_RACK = "server_rack"
    HVAC_UNIT = "hvac_unit"
    COOLING_FAN = "cooling_fan"
    ELECTRICAL_PANEL = "electrical_panel"
    CABLE = "cable"
    UPS = "ups"
    PDU = "pdu"
    FIRE_SUPPRESSION = "fire_suppression"

    # General
    VEGETATION = "vegetation"
    PERSON = "person"
    VEHICLE = "vehicle"

    # Defects & Anomalies
    DAMAGE = "damage"
    CORROSION = "corrosion"
    HOTSPOT = "hotspot"
    LEAK = "leak"
    CRACK = "crack"
    CONTAMINATION = "contamination"
    BIRD_NEST = "bird_nest"


@dataclass
class GeoLocation:
    """Geographic location with altitude."""
    latitude: float
    longitude: float
    altitude: float  # meters above sea level
    accuracy: float = 0.0  # horizontal accuracy in meters
    heading: float = 0.0  # degrees from north

    def to_dict(self) -> dict:
        return {
            "lat": self.latitude,
            "lon": self.longitude,
            "alt": self.altitude,
            "accuracy": self.accuracy,
            "heading": self.heading,
        }


@dataclass
class BoundingBox:
    """Bounding box for detected objects."""
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    @property
    def area(self) -> float:
        return self.width * self.height

    def to_xyxy(self) -> tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)

    def to_xywh(self) -> tuple[float, float, float, float]:
        return (self.x1, self.y1, self.width, self.height)


@dataclass
class Detection:
    """Single object detection result."""
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox
    mask: Optional[NDArray[np.uint8]] = None
    track_id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox": self.bbox.to_xyxy(),
            "track_id": self.track_id,
        }


@dataclass
class Segmentation:
    """Segmentation result with mask."""
    mask: NDArray[np.uint8]
    class_id: int
    class_name: str
    confidence: float
    area: int  # pixels
    centroid: tuple[int, int]

    def to_dict(self) -> dict:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "area": self.area,
            "centroid": self.centroid,
        }


@dataclass
class ThermalReading:
    """Thermal analysis data."""
    min_temp: float  # Celsius
    max_temp: float
    mean_temp: float
    hotspot_locations: list[tuple[int, int]]  # pixel coordinates
    coldspot_locations: list[tuple[int, int]]
    temperature_map: NDArray[np.float32]  # Full thermal map

    @property
    def delta_t(self) -> float:
        """Temperature differential."""
        return self.max_temp - self.min_temp

    def to_dict(self) -> dict:
        return {
            "min_temp": self.min_temp,
            "max_temp": self.max_temp,
            "mean_temp": self.mean_temp,
            "delta_t": self.delta_t,
            "hotspots": len(self.hotspot_locations),
            "coldspots": len(self.coldspot_locations),
        }


@dataclass
class Anomaly:
    """Detected anomaly or defect."""
    id: str
    type: str
    severity: SeverityLevel
    description: str
    detection: Detection
    thermal: Optional[ThermalReading] = None
    location: Optional[GeoLocation] = None
    timestamp: datetime = field(default_factory=datetime.now)
    image_path: Optional[str] = None
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "severity": self.severity.name,
            "severity_level": self.severity.value,
            "description": self.description,
            "detection": self.detection.to_dict(),
            "thermal": self.thermal.to_dict() if self.thermal else None,
            "location": self.location.to_dict() if self.location else None,
            "timestamp": self.timestamp.isoformat(),
            "image_path": self.image_path,
            "recommendations": self.recommendations,
        }


@dataclass
class FrameData:
    """Multi-sensor frame data from H30T."""
    timestamp: datetime
    frame_id: int

    # Images
    wide_image: Optional[NDArray[np.uint8]] = None
    zoom_image: Optional[NDArray[np.uint8]] = None
    thermal_image: Optional[NDArray[np.uint8]] = None  # Colorized
    thermal_raw: Optional[NDArray[np.float32]] = None  # Raw temperatures

    # Metadata
    location: Optional[GeoLocation] = None
    gimbal_attitude: Optional[tuple[float, float, float]] = None  # roll, pitch, yaw
    zoom_level: float = 1.0
    laser_distance: Optional[float] = None  # meters


@dataclass
class InspectionResult:
    """Complete inspection result for a single frame or POI."""
    frame_id: int
    timestamp: datetime
    location: Optional[GeoLocation]

    # Detection results
    detections: list[Detection] = field(default_factory=list)
    segmentations: list[Segmentation] = field(default_factory=list)

    # Thermal analysis
    thermal_reading: Optional[ThermalReading] = None

    # Anomalies
    anomalies: list[Anomaly] = field(default_factory=list)

    # VLM Analysis
    vlm_description: Optional[str] = None
    vlm_recommendations: Optional[list[str]] = None

    # Processing metrics
    inference_time_ms: float = 0.0

    @property
    def has_critical_anomaly(self) -> bool:
        return any(a.severity == SeverityLevel.CRITICAL for a in self.anomalies)

    @property
    def max_severity(self) -> SeverityLevel:
        if not self.anomalies:
            return SeverityLevel.INFO
        return max(a.severity for a in self.anomalies)

    def to_dict(self) -> dict:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp.isoformat(),
            "location": self.location.to_dict() if self.location else None,
            "detections": [d.to_dict() for d in self.detections],
            "thermal": self.thermal_reading.to_dict() if self.thermal_reading else None,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "vlm_description": self.vlm_description,
            "vlm_recommendations": self.vlm_recommendations,
            "max_severity": self.max_severity.name,
            "inference_time_ms": self.inference_time_ms,
        }


@dataclass
class InspectionSession:
    """Complete inspection session metadata."""
    session_id: str
    inspection_type: InspectionType
    start_time: datetime
    end_time: Optional[datetime] = None

    # Aircraft info
    aircraft_serial: str = ""
    pilot_id: str = ""

    # Location
    site_name: str = ""
    site_location: Optional[GeoLocation] = None

    # Results summary
    total_frames: int = 0
    total_detections: int = 0
    total_anomalies: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Files
    video_paths: list[str] = field(default_factory=list)
    report_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "inspection_type": self.inspection_type.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "aircraft_serial": self.aircraft_serial,
            "pilot_id": self.pilot_id,
            "site_name": self.site_name,
            "site_location": self.site_location.to_dict() if self.site_location else None,
            "total_frames": self.total_frames,
            "total_detections": self.total_detections,
            "total_anomalies": self.total_anomalies,
            "severity_summary": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
            },
        }
