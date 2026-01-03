"""Configuration management for BAHB inspection system."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from loguru import logger


class CameraStreamConfig(BaseModel):
    """Individual camera stream configuration."""
    enabled: bool = True
    resolution: tuple[int, int] = (1920, 1080)
    fps: int = 30
    codec: str = "h265"


class ThermalCameraConfig(BaseModel):
    """Thermal camera specific configuration."""
    enabled: bool = True
    resolution: tuple[int, int] = (640, 512)
    fps: int = 30
    fov: float = 40.6
    sensitivity: float = 0.03
    temperature_range: tuple[float, float] = (-40, 550)
    palette: str = "ironbow"
    emissivity: float = 0.95


class H30TConfig(BaseModel):
    """DJI H30T camera configuration."""
    wide: CameraStreamConfig = Field(default_factory=CameraStreamConfig)
    zoom: CameraStreamConfig = Field(default_factory=CameraStreamConfig)
    thermal: ThermalCameraConfig = Field(default_factory=ThermalCameraConfig)
    streams: dict[str, str] = Field(default_factory=lambda: {
        "wide": "rtsp://192.168.42.2:8554/wide",
        "zoom": "rtsp://192.168.42.2:8554/zoom",
        "thermal": "rtsp://192.168.42.2:8554/thermal",
    })


class YOLOConfig(BaseModel):
    """YOLOv12 model configuration."""
    enabled: bool = True
    weights: str = "models/yolov12l-inspection.engine"
    input_size: tuple[int, int] = (1280, 720)
    confidence_threshold: float = 0.35
    nms_threshold: float = 0.45
    device: str = "cuda:0"
    half_precision: bool = True
    batch_size: int = 1
    classes: list[str] = Field(default_factory=list)


class RFDETRConfig(BaseModel):
    """RF-DETR model configuration."""
    enabled: bool = True
    weights: str = "models/rf_detr_large.engine"
    backbone: str = "resnet101"
    input_size: tuple[int, int] = (640, 640)
    num_queries: int = 300
    device: str = "cuda:0"
    half_precision: bool = True
    threshold: float = 0.5


class SAM3Config(BaseModel):
    """SAM3 Nano configuration."""
    enabled: bool = True
    encoder_weights: str = "models/sam3_nano_encoder.engine"
    decoder_weights: str = "models/sam3_nano_decoder.engine"
    input_size: tuple[int, int] = (1024, 1024)
    device: str = "cuda:0"
    points_per_batch: int = 64


class QwenVLConfig(BaseModel):
    """Qwen2.5-VL-3B-AWQ configuration."""
    enabled: bool = True
    model_path: str = "models/Qwen2.5-VL-3B-AWQ"
    device: str = "cuda:0"
    max_new_tokens: int = 512
    temperature: float = 0.1
    quantization: str = "awq"
    flash_attention: bool = True
    context_length: int = 4096


class ModelsConfig(BaseModel):
    """All AI models configuration."""
    yolov12: YOLOConfig = Field(default_factory=YOLOConfig)
    rf_detr: RFDETRConfig = Field(default_factory=RFDETRConfig)
    sam3_nano: SAM3Config = Field(default_factory=SAM3Config)
    qwen_vl: QwenVLConfig = Field(default_factory=QwenVLConfig)


class ThermalZoneConfig(BaseModel):
    """Temperature zone thresholds."""
    normal_range: tuple[float, float] = (20, 60)
    warning_range: tuple[float, float] = (60, 80)
    critical_range: tuple[float, float] = (80, 150)


class ThermalAnalysisConfig(BaseModel):
    """Thermal analysis configuration."""
    enabled: bool = True
    baseline_temp: float = 25.0
    hotspot_threshold: float = 15.0
    critical_threshold: float = 40.0
    cold_spot_threshold: float = -10.0
    zones: dict[str, ThermalZoneConfig] = Field(default_factory=dict)


class InspectionProfileConfig(BaseModel):
    """Individual inspection profile."""
    enabled: bool = True
    detection_classes: list[str] = Field(default_factory=list)
    thermal_enabled: bool = True
    min_hover_time: float = 3.0


class MappingConfig(BaseModel):
    """3D mapping configuration."""
    enabled: bool = True
    overlap: int = 80
    sidelap: int = 70
    gsd: float = 0.5
    point_cloud_enabled: bool = True
    mesh_enabled: bool = True


class StreamingConfig(BaseModel):
    """Streaming configuration."""
    webrtc_enabled: bool = True
    webrtc_port: int = 8080
    rtmp_enabled: bool = False
    rtmp_url: str = ""
    recording_enabled: bool = True
    recording_format: str = "mp4"
    recording_bitrate: int = 20000000


class AlertConfig(BaseModel):
    """Alert system configuration."""
    enabled: bool = True
    mqtt_enabled: bool = True
    mqtt_broker: str = ""
    mqtt_topic: str = "bahb/alerts"
    webhook_enabled: bool = True
    webhook_url: str = ""


class SafetyConfig(BaseModel):
    """Safety configuration."""
    obstacle_avoidance: bool = True
    geofence_enabled: bool = True
    geofence_max_distance: float = 500.0
    battery_warning_level: int = 30
    battery_critical_level: int = 20
    max_wind_speed: float = 12.0


class OptimizationConfig(BaseModel):
    """Edge optimization configuration."""
    tensorrt_enabled: bool = True
    tensorrt_workspace_size: int = 4294967296
    precision: str = "fp16"
    cuda_streams: int = 4
    async_inference: bool = True
    prefetch_frames: int = 2


class Config(BaseSettings):
    """Main configuration class for BAHB system."""

    # System
    name: str = "BAHB-Inspection"
    version: str = "1.0.0"
    log_level: str = "INFO"
    data_dir: Path = Path("/data/bahb")
    cache_dir: Path = Path("/tmp/bahb_cache")
    max_workers: int = 8

    # Hardware
    gpu_memory_fraction: float = 0.9
    power_mode: str = "MAXN"

    # Components
    camera: H30TConfig = Field(default_factory=H30TConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    thermal: ThermalAnalysisConfig = Field(default_factory=ThermalAnalysisConfig)
    mapping: MappingConfig = Field(default_factory=MappingConfig)
    streaming: StreamingConfig = Field(default_factory=StreamingConfig)
    alerts: AlertConfig = Field(default_factory=AlertConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    optimization: OptimizationConfig = Field(default_factory=OptimizationConfig)

    # Inspection profiles
    profiles: dict[str, InspectionProfileConfig] = Field(default_factory=dict)

    class Config:
        env_prefix = "BAHB_"
        env_nested_delimiter = "__"

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        """Load configuration from YAML file."""
        path = Path(path)
        if not path.exists():
            logger.warning(f"Config file not found: {path}, using defaults")
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f)

        # Expand environment variables
        data = cls._expand_env_vars(data)

        return cls.model_validate(cls._flatten_config(data))

    @classmethod
    def _expand_env_vars(cls, data: Any) -> Any:
        """Recursively expand environment variables in config."""
        if isinstance(data, dict):
            return {k: cls._expand_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls._expand_env_vars(item) for item in data]
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            var_name = data[2:-1]
            return os.environ.get(var_name, "")
        return data

    @classmethod
    def _flatten_config(cls, data: dict) -> dict:
        """Flatten nested YAML structure to match Pydantic model."""
        result = {}

        # Top-level system settings
        if "system" in data:
            result.update(data["system"])

        # Hardware settings
        if "hardware" in data:
            hw = data["hardware"]
            if "manifold" in hw:
                result["gpu_memory_fraction"] = hw["manifold"].get("gpu_memory_fraction", 0.9)
                result["power_mode"] = hw["manifold"].get("power_mode", "MAXN")

        # Camera settings
        if "camera" in data and "h30t" in data["camera"]:
            result["camera"] = data["camera"]["h30t"]

        # Model settings
        if "models" in data:
            result["models"] = data["models"]

        # Other sections
        for key in ["thermal", "mapping", "streaming", "alerts", "safety", "optimization"]:
            if key in data:
                result[key] = data[key]

        # Inspection profiles
        if "inspection" in data and "profiles" in data["inspection"]:
            result["profiles"] = data["inspection"]["profiles"]

        return result

    def ensure_directories(self) -> None:
        """Create necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "inspections").mkdir(exist_ok=True)
        (self.data_dir / "models").mkdir(exist_ok=True)
        (self.data_dir / "reports").mkdir(exist_ok=True)
        (self.data_dir / "recordings").mkdir(exist_ok=True)

    def get_model_path(self, model_name: str) -> Path:
        """Get full path for a model file."""
        model_config = getattr(self.models, model_name, None)
        if model_config and hasattr(model_config, "weights"):
            return self.data_dir / model_config.weights
        return self.data_dir / "models" / model_name


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from file or environment."""
    if config_path:
        return Config.from_yaml(config_path)

    # Check default locations
    default_paths = [
        Path("configs/production.yaml"),
        Path("/etc/bahb/config.yaml"),
        Path.home() / ".bahb" / "config.yaml",
    ]

    for path in default_paths:
        if path.exists():
            logger.info(f"Loading config from: {path}")
            return Config.from_yaml(path)

    logger.warning("No config file found, using defaults")
    return Config()
