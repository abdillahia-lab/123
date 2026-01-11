"""
Configuration management for Paces renewable energy platform.

Comprehensive configuration for all modules including AI models,
weather integration, forecasting, and portfolio management.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from loguru import logger


# =============================================================================
# AI Model Configurations
# =============================================================================

class YOLOv12Config(BaseModel):
    """YOLOv12 solar/wind defect detection configuration."""
    enabled: bool = True
    weights_solar: str = "models/yolov12-solar-defects.engine"
    weights_wind: str = "models/yolov12-wind-defects.engine"
    input_size: tuple[int, int] = (1280, 720)
    confidence_threshold: float = 0.35
    nms_threshold: float = 0.45
    device: str = "cuda:0"
    half_precision: bool = True


class SAM3Config(BaseModel):
    """SAM3 Nano segmentation configuration."""
    enabled: bool = True
    encoder_weights: str = "models/sam3_nano_encoder.engine"
    decoder_weights: str = "models/sam3_nano_decoder.engine"
    device: str = "cuda:0"


class QwenVLConfig(BaseModel):
    """Qwen2.5-VL visual analysis configuration."""
    enabled: bool = True
    model_path: str = "models/Qwen2.5-VL-3B-AWQ"
    device: str = "cuda:0"
    max_new_tokens: int = 512
    temperature: float = 0.1


class ForecastingModelConfig(BaseModel):
    """Time series forecasting model configuration."""
    enabled: bool = True
    model_type: str = "temporal_fusion_transformer"
    model_path: str = "models/tft_energy_forecast.pt"
    horizon_hours: int = 48
    lookback_hours: int = 168
    device: str = "cuda:0"


class WeatherModelConfig(BaseModel):
    """Weather prediction model configuration."""
    enabled: bool = True
    model_type: str = "graphcast"  # graphcast, pangu_weather, ensemble
    api_providers: list[str] = Field(default_factory=lambda: [
        "openweathermap",
        "weatherapi",
        "visualcrossing",
    ])
    update_interval_minutes: int = 15
    forecast_days: int = 7


class AIModelsConfig(BaseModel):
    """All AI models configuration."""
    yolov12: YOLOv12Config = Field(default_factory=YOLOv12Config)
    sam3: SAM3Config = Field(default_factory=SAM3Config)
    qwen_vl: QwenVLConfig = Field(default_factory=QwenVLConfig)
    forecasting: ForecastingModelConfig = Field(default_factory=ForecastingModelConfig)
    weather: WeatherModelConfig = Field(default_factory=WeatherModelConfig)


# =============================================================================
# Module Configurations
# =============================================================================

class SolarAnalyticsConfig(BaseModel):
    """Solar farm analytics configuration."""
    enabled: bool = True
    thermal_enabled: bool = True
    hotspot_threshold_delta_c: float = 10.0
    critical_hotspot_delta_c: float = 25.0
    soiling_detection: bool = True
    shading_analysis: bool = True
    performance_ratio_target: float = 0.80
    degradation_rate_annual: float = 0.5


class WindAnalyticsConfig(BaseModel):
    """Wind farm analytics configuration."""
    enabled: bool = True
    blade_inspection_enabled: bool = True
    vibration_analysis_enabled: bool = True
    yaw_misalignment_threshold_deg: float = 5.0
    wake_loss_modeling: bool = True
    icing_detection: bool = True
    availability_target: float = 0.97


class BatteryAnalyticsConfig(BaseModel):
    """Battery storage analytics configuration."""
    enabled: bool = True
    soh_tracking: bool = True
    thermal_management: bool = True
    cell_balancing_monitoring: bool = True
    min_soc: float = 10.0
    max_soc: float = 90.0
    temperature_warning_c: float = 35.0
    temperature_critical_c: float = 45.0


class ForecastingConfig(BaseModel):
    """Energy forecasting configuration."""
    enabled: bool = True
    models: list[str] = Field(default_factory=lambda: [
        "temporal_fusion_transformer",
        "prophet",
        "ensemble",
    ])
    solar_forecast_enabled: bool = True
    wind_forecast_enabled: bool = True
    load_forecast_enabled: bool = True
    price_forecast_enabled: bool = True
    update_interval_minutes: int = 15
    ensemble_weights: dict[str, float] = Field(default_factory=lambda: {
        "tft": 0.5,
        "prophet": 0.3,
        "arima": 0.2,
    })


class GridIntegrationConfig(BaseModel):
    """Grid integration configuration."""
    enabled: bool = True
    frequency_regulation: bool = True
    voltage_support: bool = True
    ramp_rate_limit_mw_min: float = 10.0
    curtailment_response_enabled: bool = True
    market_participation: bool = True


class MaintenanceConfig(BaseModel):
    """Predictive maintenance configuration."""
    enabled: bool = True
    prediction_horizon_days: int = 30
    alert_lead_time_days: int = 7
    failure_probability_threshold: float = 0.7
    cost_optimization: bool = True


class CarbonTrackingConfig(BaseModel):
    """Carbon footprint tracking configuration."""
    enabled: bool = True
    grid_emission_factor_tco2_mwh: float = 0.4
    carbon_price_per_tonne: float = 50.0
    renewable_energy_certificates: bool = True
    lifecycle_analysis: bool = True


class FinancialConfig(BaseModel):
    """Financial analytics configuration."""
    enabled: bool = True
    currency: str = "USD"
    electricity_price_mwh: float = 50.0
    discount_rate: float = 0.08
    inflation_rate: float = 0.02
    tax_rate: float = 0.25


class AlertConfig(BaseModel):
    """Alert system configuration."""
    enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    webhook_enabled: bool = True
    webhook_url: str = ""
    escalation_enabled: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:00"


class APIConfig(BaseModel):
    """REST API configuration."""
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8080
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    rate_limit: int = 1000
    api_key_enabled: bool = True
    jwt_enabled: bool = True
    jwt_secret: str = ""


class DatabaseConfig(BaseModel):
    """Database configuration."""
    type: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    database: str = "paces"
    username: str = "paces"
    password: str = ""
    pool_size: int = 20
    timescale_enabled: bool = True  # For time-series data


class CacheConfig(BaseModel):
    """Cache configuration."""
    type: str = "redis"
    host: str = "localhost"
    port: int = 6379
    ttl_seconds: int = 300


# =============================================================================
# Main Configuration
# =============================================================================

class PacesConfig(BaseSettings):
    """Main configuration class for Paces renewable energy platform."""

    # System
    name: str = "Paces"
    version: str = "1.0.0"
    environment: str = "production"
    log_level: str = "INFO"
    data_dir: Path = Path("/data/paces")
    cache_dir: Path = Path("/tmp/paces_cache")

    # Hardware
    gpu_enabled: bool = True
    gpu_memory_fraction: float = 0.9
    max_workers: int = 16

    # AI Models
    models: AIModelsConfig = Field(default_factory=AIModelsConfig)

    # Modules
    solar: SolarAnalyticsConfig = Field(default_factory=SolarAnalyticsConfig)
    wind: WindAnalyticsConfig = Field(default_factory=WindAnalyticsConfig)
    battery: BatteryAnalyticsConfig = Field(default_factory=BatteryAnalyticsConfig)
    forecasting: ForecastingConfig = Field(default_factory=ForecastingConfig)
    grid: GridIntegrationConfig = Field(default_factory=GridIntegrationConfig)
    maintenance: MaintenanceConfig = Field(default_factory=MaintenanceConfig)
    carbon: CarbonTrackingConfig = Field(default_factory=CarbonTrackingConfig)
    financial: FinancialConfig = Field(default_factory=FinancialConfig)

    # Infrastructure
    alerts: AlertConfig = Field(default_factory=AlertConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

    # Integration with BAHB drone inspection
    bahb_integration_enabled: bool = True
    bahb_config_path: str = ""

    class Config:
        env_prefix = "PACES_"
        env_nested_delimiter = "__"

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PacesConfig":
        """Load configuration from YAML file."""
        path = Path(path)
        if not path.exists():
            logger.warning(f"Config file not found: {path}, using defaults")
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f)

        data = cls._expand_env_vars(data)
        return cls.model_validate(data)

    @classmethod
    def _expand_env_vars(cls, data: Any) -> Any:
        """Recursively expand environment variables."""
        if isinstance(data, dict):
            return {k: cls._expand_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls._expand_env_vars(item) for item in data]
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            var_name = data[2:-1]
            default = ""
            if ":" in var_name:
                var_name, default = var_name.split(":", 1)
            return os.environ.get(var_name, default)
        return data

    def ensure_directories(self) -> None:
        """Create necessary directories."""
        dirs = [
            self.data_dir,
            self.cache_dir,
            self.data_dir / "models",
            self.data_dir / "inspections",
            self.data_dir / "forecasts",
            self.data_dir / "reports",
            self.data_dir / "exports",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def get_model_path(self, model_name: str) -> Path:
        """Get full path for a model file."""
        return self.data_dir / "models" / model_name


def load_paces_config(config_path: Optional[str] = None) -> PacesConfig:
    """Load Paces configuration from file or environment."""
    if config_path:
        return PacesConfig.from_yaml(config_path)

    default_paths = [
        Path("configs/paces.yaml"),
        Path("/etc/paces/config.yaml"),
        Path.home() / ".paces" / "config.yaml",
    ]

    for path in default_paths:
        if path.exists():
            logger.info(f"Loading Paces config from: {path}")
            return PacesConfig.from_yaml(path)

    logger.warning("No Paces config file found, using defaults")
    return PacesConfig()
