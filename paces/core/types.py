"""
Core type definitions for Paces renewable energy platform.

Comprehensive data models for solar, wind, battery, and grid assets
with support for AI-driven analytics and predictive maintenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Optional, Any
from uuid import uuid4
import numpy as np
from numpy.typing import NDArray


# =============================================================================
# Enums
# =============================================================================

class AssetType(Enum):
    """Types of renewable energy assets."""
    SOLAR_PANEL = "solar_panel"
    SOLAR_ARRAY = "solar_array"
    SOLAR_FARM = "solar_farm"
    WIND_TURBINE = "wind_turbine"
    WIND_FARM = "wind_farm"
    BATTERY_CELL = "battery_cell"
    BATTERY_MODULE = "battery_module"
    BATTERY_SYSTEM = "battery_system"
    INVERTER = "inverter"
    TRANSFORMER = "transformer"
    SUBSTATION = "substation"
    TRANSMISSION_LINE = "transmission_line"
    GRID_CONNECTION = "grid_connection"


class EnergySource(Enum):
    """Energy source types."""
    SOLAR_PV = "solar_pv"
    SOLAR_THERMAL = "solar_thermal"
    WIND_ONSHORE = "wind_onshore"
    WIND_OFFSHORE = "wind_offshore"
    HYDRO = "hydro"
    GEOTHERMAL = "geothermal"
    BIOMASS = "biomass"
    BATTERY_STORAGE = "battery_storage"
    GRID = "grid"


class MaintenanceStatus(Enum):
    """Asset maintenance status."""
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    MAINTENANCE_REQUIRED = "maintenance_required"
    MAINTENANCE_SCHEDULED = "maintenance_scheduled"
    UNDER_MAINTENANCE = "under_maintenance"
    OFFLINE = "offline"
    CRITICAL = "critical"
    DECOMMISSIONED = "decommissioned"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class WeatherCondition(Enum):
    """Weather condition types."""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    FOG = "fog"
    LIGHT_RAIN = "light_rain"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    THUNDERSTORM = "thunderstorm"
    SNOW = "snow"
    HAIL = "hail"
    DUST = "dust"


class DefectType(Enum):
    """Defect types for renewable assets."""
    # Solar defects
    CELL_CRACK = "cell_crack"
    HOT_SPOT = "hot_spot"
    SNAIL_TRAIL = "snail_trail"
    DELAMINATION = "delamination"
    DISCOLORATION = "discoloration"
    SOILING = "soiling"
    SHADING = "shading"
    PID = "potential_induced_degradation"
    BYPASS_DIODE_FAILURE = "bypass_diode_failure"
    JUNCTION_BOX_FAILURE = "junction_box_failure"

    # Wind defects
    BLADE_CRACK = "blade_crack"
    BLADE_EROSION = "blade_erosion"
    LIGHTNING_STRIKE = "lightning_strike"
    ICE_BUILDUP = "ice_buildup"
    GEARBOX_WEAR = "gearbox_wear"
    BEARING_FAILURE = "bearing_failure"
    YAW_MISALIGNMENT = "yaw_misalignment"
    PITCH_MALFUNCTION = "pitch_malfunction"

    # Battery defects
    THERMAL_RUNAWAY = "thermal_runaway"
    CAPACITY_FADE = "capacity_fade"
    INTERNAL_SHORT = "internal_short"
    ELECTROLYTE_LEAK = "electrolyte_leak"
    SWELLING = "swelling"

    # General
    CORROSION = "corrosion"
    CONNECTOR_DAMAGE = "connector_damage"
    CABLE_DAMAGE = "cable_damage"
    STRUCTURAL_DAMAGE = "structural_damage"


class ForecastModel(Enum):
    """Forecasting model types."""
    TEMPORAL_FUSION = "temporal_fusion_transformer"
    TIMEGPT = "timegpt"
    CHRONOS = "chronos"
    PROPHET = "prophet"
    LSTM = "lstm"
    ENSEMBLE = "ensemble"


# =============================================================================
# Base Data Classes
# =============================================================================

@dataclass
class GeoLocation:
    """Geographic location with full metadata."""
    latitude: float
    longitude: float
    altitude: float = 0.0
    accuracy: float = 0.0
    timezone: str = "UTC"

    def distance_to(self, other: GeoLocation) -> float:
        """Calculate distance in km using Haversine formula."""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth radius in km
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def to_dict(self) -> dict:
        return {
            "lat": self.latitude,
            "lon": self.longitude,
            "alt": self.altitude,
            "accuracy": self.accuracy,
            "timezone": self.timezone,
        }


@dataclass
class TimeSeriesPoint:
    """Single point in a time series."""
    timestamp: datetime
    value: float
    unit: str = ""
    quality: float = 1.0  # Data quality score 0-1

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "unit": self.unit,
            "quality": self.quality,
        }


@dataclass
class TimeSeries:
    """Time series data container."""
    name: str
    points: list[TimeSeriesPoint] = field(default_factory=list)
    unit: str = ""
    resolution_seconds: int = 3600

    @property
    def values(self) -> NDArray[np.float64]:
        return np.array([p.value for p in self.points])

    @property
    def timestamps(self) -> list[datetime]:
        return [p.timestamp for p in self.points]

    def resample(self, resolution_seconds: int) -> TimeSeries:
        """Resample time series to new resolution."""
        # Implementation would use pandas-like resampling
        return self

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "unit": self.unit,
            "resolution_seconds": self.resolution_seconds,
            "points": [p.to_dict() for p in self.points],
        }


# =============================================================================
# Weather Data
# =============================================================================

@dataclass
class WeatherData:
    """Comprehensive weather data for a location."""
    timestamp: datetime
    location: GeoLocation

    # Temperature
    temperature_c: float = 20.0
    feels_like_c: float = 20.0
    dew_point_c: float = 10.0

    # Solar radiation
    ghi: float = 0.0  # Global Horizontal Irradiance (W/m2)
    dni: float = 0.0  # Direct Normal Irradiance (W/m2)
    dhi: float = 0.0  # Diffuse Horizontal Irradiance (W/m2)

    # Wind
    wind_speed_ms: float = 0.0
    wind_gust_ms: float = 0.0
    wind_direction_deg: float = 0.0

    # Atmosphere
    humidity_pct: float = 50.0
    pressure_hpa: float = 1013.25
    cloud_cover_pct: float = 0.0
    visibility_km: float = 10.0

    # Precipitation
    precipitation_mm: float = 0.0
    precipitation_probability: float = 0.0
    snow_depth_cm: float = 0.0

    # Conditions
    condition: WeatherCondition = WeatherCondition.CLEAR
    uv_index: float = 0.0
    air_quality_index: int = 50

    @property
    def is_optimal_solar(self) -> bool:
        """Check if conditions are optimal for solar production."""
        return (
            self.ghi > 600 and
            self.cloud_cover_pct < 20 and
            self.temperature_c < 35 and
            self.condition in [WeatherCondition.CLEAR, WeatherCondition.PARTLY_CLOUDY]
        )

    @property
    def is_optimal_wind(self) -> bool:
        """Check if conditions are optimal for wind production."""
        return (
            5 <= self.wind_speed_ms <= 25 and
            self.precipitation_mm < 1 and
            self.visibility_km > 5
        )

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "location": self.location.to_dict(),
            "temperature_c": self.temperature_c,
            "ghi": self.ghi,
            "dni": self.dni,
            "dhi": self.dhi,
            "wind_speed_ms": self.wind_speed_ms,
            "wind_direction_deg": self.wind_direction_deg,
            "humidity_pct": self.humidity_pct,
            "cloud_cover_pct": self.cloud_cover_pct,
            "condition": self.condition.value,
        }


@dataclass
class WeatherForecast:
    """Weather forecast for a location."""
    location: GeoLocation
    generated_at: datetime
    model: str = "ensemble"
    hourly: list[WeatherData] = field(default_factory=list)
    daily_summary: list[dict] = field(default_factory=list)
    confidence: float = 0.9


# =============================================================================
# Energy Readings
# =============================================================================

@dataclass
class EnergyReading:
    """Energy production/consumption reading."""
    timestamp: datetime
    asset_id: str

    # Power
    power_kw: float = 0.0
    power_factor: float = 1.0

    # Energy
    energy_kwh: float = 0.0
    energy_cumulative_kwh: float = 0.0

    # Electrical
    voltage_v: float = 0.0
    current_a: float = 0.0
    frequency_hz: float = 50.0

    # Efficiency
    efficiency_pct: float = 0.0
    capacity_factor: float = 0.0

    # Environmental
    ambient_temp_c: float = 25.0
    module_temp_c: Optional[float] = None
    irradiance_wm2: Optional[float] = None
    wind_speed_ms: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "asset_id": self.asset_id,
            "power_kw": self.power_kw,
            "energy_kwh": self.energy_kwh,
            "efficiency_pct": self.efficiency_pct,
            "capacity_factor": self.capacity_factor,
        }


@dataclass
class PowerForecast:
    """Power production forecast."""
    asset_id: str
    generated_at: datetime
    model: ForecastModel
    horizon_hours: int

    # Forecasted values
    timestamps: list[datetime] = field(default_factory=list)
    power_kw: list[float] = field(default_factory=list)
    energy_kwh: list[float] = field(default_factory=list)

    # Uncertainty bounds
    lower_bound_kw: list[float] = field(default_factory=list)
    upper_bound_kw: list[float] = field(default_factory=list)
    confidence_intervals: list[float] = field(default_factory=list)

    # Accuracy metrics
    mae: float = 0.0
    rmse: float = 0.0
    mape: float = 0.0

    @property
    def total_energy_kwh(self) -> float:
        return sum(self.energy_kwh)

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "generated_at": self.generated_at.isoformat(),
            "model": self.model.value,
            "horizon_hours": self.horizon_hours,
            "total_energy_kwh": self.total_energy_kwh,
            "mae": self.mae,
            "rmse": self.rmse,
        }


# =============================================================================
# Defects and Anomalies
# =============================================================================

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


@dataclass
class Defect:
    """Detected defect on a renewable asset."""
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    asset_id: str = ""
    defect_type: DefectType = DefectType.HOT_SPOT
    severity: AlertSeverity = AlertSeverity.MEDIUM

    # Detection
    confidence: float = 0.0
    bbox: Optional[BoundingBox] = None
    mask: Optional[NDArray[np.uint8]] = None

    # Location
    location: Optional[GeoLocation] = None
    position_on_asset: Optional[tuple[float, float]] = None

    # Thermal
    temperature_c: Optional[float] = None
    delta_t: Optional[float] = None

    # Analysis
    description: str = ""
    ai_analysis: str = ""
    recommendations: list[str] = field(default_factory=list)
    estimated_impact_pct: float = 0.0

    # Metadata
    detected_at: datetime = field(default_factory=datetime.now)
    image_path: Optional[str] = None
    thermal_image_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "defect_type": self.defect_type.value,
            "severity": self.severity.name,
            "confidence": self.confidence,
            "description": self.description,
            "recommendations": self.recommendations,
            "estimated_impact_pct": self.estimated_impact_pct,
            "detected_at": self.detected_at.isoformat(),
        }


# =============================================================================
# Renewable Assets
# =============================================================================

@dataclass
class RenewableAsset:
    """Base class for all renewable energy assets."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    asset_type: AssetType = AssetType.SOLAR_PANEL
    location: Optional[GeoLocation] = None

    # Capacity
    rated_capacity_kw: float = 0.0
    actual_capacity_kw: float = 0.0

    # Status
    status: MaintenanceStatus = MaintenanceStatus.OPERATIONAL
    health_score: float = 100.0  # 0-100
    efficiency: float = 1.0  # 0-1

    # Dates
    installation_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    next_scheduled_maintenance: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None

    # Defects
    defects: list[Defect] = field(default_factory=list)

    # Metadata
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def age_years(self) -> float:
        if self.installation_date:
            return (datetime.now() - self.installation_date).days / 365.25
        return 0.0

    @property
    def active_defects(self) -> list[Defect]:
        return [d for d in self.defects if d.severity.value >= AlertSeverity.LOW.value]

    @property
    def degradation_pct(self) -> float:
        if self.rated_capacity_kw > 0:
            return (1 - self.actual_capacity_kw / self.rated_capacity_kw) * 100
        return 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "asset_type": self.asset_type.value,
            "rated_capacity_kw": self.rated_capacity_kw,
            "actual_capacity_kw": self.actual_capacity_kw,
            "status": self.status.value,
            "health_score": self.health_score,
            "efficiency": self.efficiency,
            "age_years": self.age_years,
            "degradation_pct": self.degradation_pct,
            "active_defects": len(self.active_defects),
        }


# =============================================================================
# Solar Assets
# =============================================================================

@dataclass
class SolarPanel(RenewableAsset):
    """Individual solar panel."""
    asset_type: AssetType = field(default=AssetType.SOLAR_PANEL)

    # Panel specs
    cell_type: str = "monocrystalline"  # mono, poly, thin-film
    cell_count: int = 72
    panel_wattage: float = 400.0

    # Electrical
    voc: float = 48.0  # Open circuit voltage
    isc: float = 10.0  # Short circuit current
    vmp: float = 40.0  # Voltage at max power
    imp: float = 10.0  # Current at max power

    # Temperature coefficients
    temp_coeff_pmax: float = -0.35  # %/C
    temp_coeff_voc: float = -0.28  # %/C
    temp_coeff_isc: float = 0.05  # %/C

    # Physical
    area_m2: float = 2.0
    weight_kg: float = 22.0
    tilt_angle: float = 30.0
    azimuth: float = 180.0  # 180 = South

    # Current conditions
    current_temp_c: float = 25.0
    current_irradiance: float = 0.0
    current_power_w: float = 0.0

    # String position
    string_id: str = ""
    position_in_string: int = 0

    def calculate_power_output(
        self,
        irradiance_wm2: float,
        ambient_temp_c: float,
        noct: float = 45.0,
    ) -> float:
        """Calculate expected power output under current conditions."""
        if irradiance_wm2 <= 0:
            return 0.0

        # Cell temperature
        cell_temp = ambient_temp_c + (noct - 20) * (irradiance_wm2 / 800)

        # Temperature derating
        temp_diff = cell_temp - 25  # STC is 25C
        temp_factor = 1 + (self.temp_coeff_pmax / 100) * temp_diff

        # Irradiance factor
        irrad_factor = irradiance_wm2 / 1000  # STC is 1000 W/m2

        # Calculated power
        power = self.panel_wattage * irrad_factor * temp_factor * self.efficiency

        return max(0.0, power)


@dataclass
class SolarArray:
    """Array of solar panels (string or group)."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    panels: list[SolarPanel] = field(default_factory=list)
    inverter_id: str = ""

    # Configuration
    strings_count: int = 1
    panels_per_string: int = 20

    # Electrical
    dc_voltage: float = 0.0
    dc_current: float = 0.0
    ac_power_kw: float = 0.0

    @property
    def rated_capacity_kw(self) -> float:
        return sum(p.panel_wattage for p in self.panels) / 1000

    @property
    def current_power_kw(self) -> float:
        return sum(p.current_power_w for p in self.panels) / 1000

    @property
    def health_score(self) -> float:
        if not self.panels:
            return 100.0
        return sum(p.health_score for p in self.panels) / len(self.panels)

    @property
    def defect_count(self) -> int:
        return sum(len(p.active_defects) for p in self.panels)


@dataclass
class SolarFarm(RenewableAsset):
    """Complete solar farm installation."""
    asset_type: AssetType = field(default=AssetType.SOLAR_FARM)

    arrays: list[SolarArray] = field(default_factory=list)
    inverters: list[str] = field(default_factory=list)  # inverter IDs

    # Farm specs
    total_panels: int = 0
    total_area_hectares: float = 0.0
    dc_capacity_mw: float = 0.0
    ac_capacity_mw: float = 0.0

    # Performance
    lifetime_energy_mwh: float = 0.0
    annual_energy_mwh: float = 0.0
    capacity_factor: float = 0.0
    performance_ratio: float = 0.0

    # Grid connection
    grid_connection_id: str = ""
    ppa_price_kwh: float = 0.0

    @property
    def current_power_mw(self) -> float:
        return sum(a.current_power_kw for a in self.arrays) / 1000

    @property
    def total_defects(self) -> int:
        return sum(a.defect_count for a in self.arrays)

    def get_performance_metrics(self) -> dict:
        return {
            "current_power_mw": self.current_power_mw,
            "capacity_factor": self.capacity_factor,
            "performance_ratio": self.performance_ratio,
            "health_score": self.health_score,
            "total_defects": self.total_defects,
            "lifetime_energy_mwh": self.lifetime_energy_mwh,
        }


# =============================================================================
# Wind Assets
# =============================================================================

@dataclass
class WindTurbine(RenewableAsset):
    """Individual wind turbine."""
    asset_type: AssetType = field(default=AssetType.WIND_TURBINE)

    # Turbine specs
    hub_height_m: float = 80.0
    rotor_diameter_m: float = 100.0
    blade_count: int = 3

    # Power curve
    cut_in_speed_ms: float = 3.0
    rated_speed_ms: float = 12.0
    cut_out_speed_ms: float = 25.0
    survival_speed_ms: float = 50.0

    # Current state
    rotor_speed_rpm: float = 0.0
    generator_speed_rpm: float = 0.0
    pitch_angle_deg: float = 0.0
    yaw_angle_deg: float = 0.0

    # Nacelle data
    nacelle_temp_c: float = 25.0
    gearbox_oil_temp_c: float = 50.0
    generator_temp_c: float = 60.0

    # Vibration analysis
    tower_vibration: float = 0.0
    nacelle_vibration: float = 0.0
    drivetrain_vibration: float = 0.0

    # Production
    current_power_kw: float = 0.0
    wind_speed_ms: float = 0.0
    wind_direction_deg: float = 0.0

    @property
    def rotor_area_m2(self) -> float:
        return np.pi * (self.rotor_diameter_m / 2) ** 2

    @property
    def tip_speed_ratio(self) -> float:
        if self.wind_speed_ms > 0:
            tip_speed = self.rotor_speed_rpm * np.pi * self.rotor_diameter_m / 60
            return tip_speed / self.wind_speed_ms
        return 0.0

    def calculate_power_output(
        self,
        wind_speed_ms: float,
        air_density: float = 1.225,
    ) -> float:
        """Calculate expected power from wind speed."""
        if wind_speed_ms < self.cut_in_speed_ms:
            return 0.0
        if wind_speed_ms > self.cut_out_speed_ms:
            return 0.0
        if wind_speed_ms >= self.rated_speed_ms:
            return self.rated_capacity_kw * 1000

        # Cubic relationship in operating region
        cp = 0.45  # Power coefficient (typical)
        power = 0.5 * air_density * self.rotor_area_m2 * (wind_speed_ms ** 3) * cp

        return min(power, self.rated_capacity_kw * 1000)


@dataclass
class WindFarm(RenewableAsset):
    """Complete wind farm installation."""
    asset_type: AssetType = field(default=AssetType.WIND_FARM)

    turbines: list[WindTurbine] = field(default_factory=list)

    # Farm specs
    total_area_km2: float = 0.0
    terrain_type: str = "onshore"  # onshore, offshore, complex

    # Performance
    lifetime_energy_mwh: float = 0.0
    annual_energy_mwh: float = 0.0
    capacity_factor: float = 0.0
    availability: float = 0.0

    # Wake effects
    wake_loss_pct: float = 5.0

    # Grid connection
    grid_connection_id: str = ""
    ppa_price_kwh: float = 0.0

    @property
    def current_power_mw(self) -> float:
        return sum(t.current_power_kw for t in self.turbines) / 1000

    @property
    def average_wind_speed(self) -> float:
        if not self.turbines:
            return 0.0
        return sum(t.wind_speed_ms for t in self.turbines) / len(self.turbines)

    @property
    def turbines_online(self) -> int:
        return sum(1 for t in self.turbines if t.status == MaintenanceStatus.OPERATIONAL)


# =============================================================================
# Battery Storage
# =============================================================================

@dataclass
class BatteryCell:
    """Individual battery cell."""
    id: str = field(default_factory=lambda: str(uuid4())[:8])

    # Cell specs
    chemistry: str = "NMC"  # NMC, LFP, NCA, etc.
    nominal_voltage: float = 3.7
    capacity_ah: float = 50.0

    # State
    voltage: float = 3.7
    current: float = 0.0
    soc: float = 50.0  # State of charge (%)
    soh: float = 100.0  # State of health (%)
    temperature_c: float = 25.0

    # Limits
    max_voltage: float = 4.2
    min_voltage: float = 2.5
    max_charge_current: float = 50.0
    max_discharge_current: float = 100.0
    max_temp_c: float = 45.0
    min_temp_c: float = 0.0

    # Cycle data
    cycle_count: int = 0
    energy_throughput_kwh: float = 0.0


@dataclass
class BatteryModule(RenewableAsset):
    """Battery module (group of cells)."""
    asset_type: AssetType = field(default=AssetType.BATTERY_MODULE)

    cells: list[BatteryCell] = field(default_factory=list)

    # Configuration
    cells_series: int = 16
    cells_parallel: int = 4

    # Module state
    voltage: float = 0.0
    current: float = 0.0
    soc: float = 50.0
    soh: float = 100.0
    power_kw: float = 0.0

    # Balancing
    cell_imbalance_mv: float = 0.0
    balancing_active: bool = False

    @property
    def energy_capacity_kwh(self) -> float:
        if not self.cells:
            return 0.0
        cell = self.cells[0]
        return (
            cell.nominal_voltage * self.cells_series *
            cell.capacity_ah * self.cells_parallel / 1000
        )

    @property
    def available_energy_kwh(self) -> float:
        return self.energy_capacity_kwh * (self.soc / 100) * (self.soh / 100)


@dataclass
class BatterySystem(RenewableAsset):
    """Complete battery energy storage system (BESS)."""
    asset_type: AssetType = field(default=AssetType.BATTERY_SYSTEM)

    modules: list[BatteryModule] = field(default_factory=list)

    # System specs
    energy_capacity_mwh: float = 0.0
    power_capacity_mw: float = 0.0
    round_trip_efficiency: float = 0.90

    # State
    soc: float = 50.0
    soh: float = 100.0
    power_kw: float = 0.0  # Positive = charging, negative = discharging

    # Operating mode
    mode: str = "standby"  # charging, discharging, standby, maintenance

    # Thermal management
    hvac_power_kw: float = 0.0
    avg_temperature_c: float = 25.0

    # Lifetime
    total_cycles: int = 0
    lifetime_throughput_mwh: float = 0.0

    # Grid services
    frequency_regulation: bool = True
    peak_shaving: bool = True
    arbitrage: bool = True

    @property
    def available_energy_mwh(self) -> float:
        return self.energy_capacity_mwh * (self.soc / 100) * (self.soh / 100)

    @property
    def charge_power_available_mw(self) -> float:
        charge_headroom = (100 - self.soc) / 100
        return self.power_capacity_mw * charge_headroom

    @property
    def discharge_power_available_mw(self) -> float:
        discharge_headroom = self.soc / 100
        return self.power_capacity_mw * discharge_headroom


# =============================================================================
# Grid Integration
# =============================================================================

@dataclass
class GridConnection:
    """Grid interconnection point."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    location: Optional[GeoLocation] = None

    # Connection specs
    voltage_kv: float = 33.0
    connection_capacity_mva: float = 100.0
    export_limit_mw: float = 100.0
    import_limit_mw: float = 50.0

    # Current state
    power_export_mw: float = 0.0
    power_import_mw: float = 0.0
    voltage_pu: float = 1.0
    frequency_hz: float = 50.0
    power_factor: float = 0.95

    # Grid signals
    curtailment_active: bool = False
    curtailment_limit_mw: float = 0.0

    # Pricing
    spot_price_mwh: float = 50.0
    feed_in_tariff_mwh: float = 0.0

    # Connected assets
    connected_asset_ids: list[str] = field(default_factory=list)


# =============================================================================
# Maintenance
# =============================================================================

@dataclass
class MaintenanceEvent:
    """Maintenance event record."""
    id: str = field(default_factory=lambda: str(uuid4()))
    asset_id: str = ""

    # Event details
    event_type: str = "scheduled"  # scheduled, corrective, predictive, emergency
    description: str = ""

    # Scheduling
    scheduled_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_hours: float = 0.0

    # Resources
    technicians: list[str] = field(default_factory=list)
    parts_used: list[dict] = field(default_factory=list)

    # Costs
    labor_cost: float = 0.0
    parts_cost: float = 0.0
    total_cost: float = 0.0

    # Impact
    production_loss_mwh: float = 0.0
    revenue_loss: float = 0.0

    # Related
    defect_ids: list[str] = field(default_factory=list)
    work_order_id: str = ""
    notes: str = ""

    @property
    def is_complete(self) -> bool:
        return self.completed_at is not None


# =============================================================================
# Financial & Carbon
# =============================================================================

@dataclass
class CarbonMetrics:
    """Carbon and emissions tracking."""
    timestamp: datetime = field(default_factory=datetime.now)
    asset_id: str = ""
    period: str = "daily"  # hourly, daily, monthly, yearly

    # Avoided emissions
    co2_avoided_tonnes: float = 0.0
    grid_emission_factor: float = 0.4  # tCO2/MWh

    # Energy production
    clean_energy_mwh: float = 0.0

    # Carbon credits
    carbon_credits_earned: float = 0.0
    carbon_price_tonne: float = 50.0
    carbon_revenue: float = 0.0

    # Lifecycle emissions
    embodied_carbon_tonnes: float = 0.0
    operational_carbon_tonnes: float = 0.0
    net_carbon_benefit_tonnes: float = 0.0

    @property
    def carbon_intensity_gco2_kwh(self) -> float:
        if self.clean_energy_mwh > 0:
            return (self.operational_carbon_tonnes * 1000000) / (self.clean_energy_mwh * 1000)
        return 0.0


@dataclass
class FinancialMetrics:
    """Financial performance metrics."""
    timestamp: datetime = field(default_factory=datetime.now)
    asset_id: str = ""
    period: str = "monthly"  # daily, monthly, quarterly, yearly

    # Revenue
    energy_revenue: float = 0.0
    capacity_revenue: float = 0.0
    ancillary_revenue: float = 0.0
    carbon_credit_revenue: float = 0.0
    total_revenue: float = 0.0

    # Costs
    opex: float = 0.0
    maintenance_cost: float = 0.0
    insurance_cost: float = 0.0
    land_lease: float = 0.0
    grid_charges: float = 0.0
    total_costs: float = 0.0

    # Profitability
    ebitda: float = 0.0
    net_income: float = 0.0

    # Production
    energy_produced_mwh: float = 0.0
    energy_sold_mwh: float = 0.0
    curtailed_mwh: float = 0.0

    # Prices
    avg_price_mwh: float = 0.0
    ppa_price_mwh: float = 0.0
    spot_price_mwh: float = 0.0

    # KPIs
    capacity_factor: float = 0.0
    availability: float = 0.0
    lcoe: float = 0.0  # Levelized cost of energy

    @property
    def profit_margin(self) -> float:
        if self.total_revenue > 0:
            return (self.total_revenue - self.total_costs) / self.total_revenue
        return 0.0


# =============================================================================
# Portfolio
# =============================================================================

@dataclass
class Portfolio:
    """Renewable energy portfolio."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    owner: str = ""

    # Assets
    solar_farms: list[SolarFarm] = field(default_factory=list)
    wind_farms: list[WindFarm] = field(default_factory=list)
    battery_systems: list[BatterySystem] = field(default_factory=list)
    grid_connections: list[GridConnection] = field(default_factory=list)

    # Aggregated metrics
    total_capacity_mw: float = 0.0
    total_storage_mwh: float = 0.0

    @property
    def solar_capacity_mw(self) -> float:
        return sum(f.dc_capacity_mw for f in self.solar_farms)

    @property
    def wind_capacity_mw(self) -> float:
        return sum(f.rated_capacity_kw for f in self.wind_farms) / 1000

    @property
    def storage_capacity_mwh(self) -> float:
        return sum(b.energy_capacity_mwh for b in self.battery_systems)

    @property
    def current_generation_mw(self) -> float:
        solar = sum(f.current_power_mw for f in self.solar_farms)
        wind = sum(f.current_power_mw for f in self.wind_farms)
        return solar + wind

    @property
    def total_assets(self) -> int:
        return (
            len(self.solar_farms) +
            len(self.wind_farms) +
            len(self.battery_systems)
        )

    def get_summary(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "solar_capacity_mw": self.solar_capacity_mw,
            "wind_capacity_mw": self.wind_capacity_mw,
            "storage_capacity_mwh": self.storage_capacity_mwh,
            "current_generation_mw": self.current_generation_mw,
            "total_assets": self.total_assets,
        }
