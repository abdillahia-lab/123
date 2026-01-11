"""
Core type definitions for Paces renewable energy site development platform.

Comprehensive data models for parcels, projects, permits, grid connections,
environmental constraints, and site scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum, auto
from typing import Optional, Any
from uuid import uuid4
import json


# =============================================================================
# Enumerations
# =============================================================================

class ProjectType(Enum):
    """Types of renewable energy projects."""
    UTILITY_SOLAR = "utility_solar"
    COMMERCIAL_SOLAR = "commercial_solar"
    COMMUNITY_SOLAR = "community_solar"
    ROOFTOP_SOLAR = "rooftop_solar"
    AGRIVOLTAICS = "agrivoltaics"
    FLOATING_SOLAR = "floating_solar"
    WIND_ONSHORE = "wind_onshore"
    WIND_OFFSHORE = "wind_offshore"
    BATTERY_STORAGE = "battery_storage"
    HYBRID_SOLAR_STORAGE = "hybrid_solar_storage"
    EV_CHARGING = "ev_charging"
    HYDROGEN = "hydrogen"
    DATA_CENTER = "data_center"


class ProjectStatus(Enum):
    """Project development stages."""
    PROSPECTING = "prospecting"
    SITE_CONTROL = "site_control"
    PERMITTING = "permitting"
    INTERCONNECTION = "interconnection"
    FINANCING = "financing"
    CONSTRUCTION = "construction"
    OPERATIONAL = "operational"
    DECOMMISSIONED = "decommissioned"
    CANCELLED = "cancelled"


class PermitStatus(Enum):
    """Permitting status."""
    NOT_STARTED = "not_started"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    DENIED = "denied"
    APPEALED = "appealed"
    EXPIRED = "expired"


class ZoningType(Enum):
    """Zoning classifications."""
    AGRICULTURAL = "agricultural"
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    CONSERVATION = "conservation"
    UTILITY = "utility"
    UNKNOWN = "unknown"


class LandUsePermission(Enum):
    """Solar/renewable energy permission status."""
    BY_RIGHT = "by_right"  # Allowed without special permit
    CONDITIONAL_USE = "conditional_use"  # Requires CUP
    SPECIAL_EXCEPTION = "special_exception"
    VARIANCE_REQUIRED = "variance_required"
    PROHIBITED = "prohibited"
    MORATORIUM = "moratorium"
    UNKNOWN = "unknown"


class InterconnectionStatus(Enum):
    """Grid interconnection queue status."""
    NOT_APPLIED = "not_applied"
    APPLICATION_SUBMITTED = "application_submitted"
    FEASIBILITY_STUDY = "feasibility_study"
    SYSTEM_IMPACT_STUDY = "system_impact_study"
    FACILITIES_STUDY = "facilities_study"
    INTERCONNECTION_AGREEMENT = "interconnection_agreement"
    CONSTRUCTION = "construction"
    OPERATIONAL = "operational"
    WITHDRAWN = "withdrawn"


class EnvironmentalRisk(Enum):
    """Environmental constraint risk levels."""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    FATAL = 4


class Utility(Enum):
    """Major utility companies."""
    DUKE_ENERGY = "duke_energy"
    DOMINION = "dominion"
    NEXTERA = "nextera"
    SOUTHERN_COMPANY = "southern_company"
    AEP = "aep"
    XCEL = "xcel"
    PGE = "pge"
    SCE = "sce"
    ERCOT = "ercot"
    PJM = "pjm"
    MISO = "miso"
    CAISO = "caiso"
    SPP = "spp"
    NYISO = "nyiso"
    ISO_NE = "iso_ne"
    OTHER = "other"


# =============================================================================
# Geographic Types
# =============================================================================

@dataclass
class GeoPoint:
    """Geographic point coordinate."""
    latitude: float
    longitude: float

    def to_tuple(self) -> tuple[float, float]:
        return (self.latitude, self.longitude)

    def to_dict(self) -> dict:
        return {"lat": self.latitude, "lng": self.longitude}

    def distance_to(self, other: GeoPoint) -> float:
        """Calculate distance in kilometers using Haversine formula."""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth's radius in km
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c


@dataclass
class BoundingBox:
    """Geographic bounding box."""
    min_lat: float
    min_lng: float
    max_lat: float
    max_lng: float

    @property
    def center(self) -> GeoPoint:
        return GeoPoint(
            latitude=(self.min_lat + self.max_lat) / 2,
            longitude=(self.min_lng + self.max_lng) / 2,
        )

    def contains(self, point: GeoPoint) -> bool:
        return (
            self.min_lat <= point.latitude <= self.max_lat and
            self.min_lng <= point.longitude <= self.max_lng
        )


@dataclass
class GeoPolygon:
    """Geographic polygon defined by vertices."""
    vertices: list[GeoPoint] = field(default_factory=list)

    @property
    def centroid(self) -> GeoPoint:
        if not self.vertices:
            return GeoPoint(0, 0)
        avg_lat = sum(v.latitude for v in self.vertices) / len(self.vertices)
        avg_lng = sum(v.longitude for v in self.vertices) / len(self.vertices)
        return GeoPoint(avg_lat, avg_lng)

    @property
    def bounding_box(self) -> BoundingBox:
        if not self.vertices:
            return BoundingBox(0, 0, 0, 0)
        lats = [v.latitude for v in self.vertices]
        lngs = [v.longitude for v in self.vertices]
        return BoundingBox(min(lats), min(lngs), max(lats), max(lngs))

    def to_geojson(self) -> dict:
        return {
            "type": "Polygon",
            "coordinates": [[[v.longitude, v.latitude] for v in self.vertices]],
        }


# =============================================================================
# Parcel / Land Types
# =============================================================================

@dataclass
class Parcel:
    """Land parcel for potential development."""
    id: str = field(default_factory=lambda: str(uuid4()))
    apn: str = ""  # Assessor's Parcel Number

    # Location
    state: str = ""
    county: str = ""
    municipality: str = ""
    address: str = ""
    centroid: Optional[GeoPoint] = None
    boundary: Optional[GeoPolygon] = None

    # Physical characteristics
    acreage: float = 0.0
    usable_acreage: float = 0.0

    # Ownership
    owner_name: str = ""
    owner_address: str = ""
    owner_type: str = ""  # individual, corporation, government, etc.

    # Zoning
    zoning_code: str = ""
    zoning_type: ZoningType = ZoningType.UNKNOWN
    zoning_description: str = ""
    solar_permission: LandUsePermission = LandUsePermission.UNKNOWN

    # Valuation
    assessed_value: float = 0.0
    market_value: float = 0.0
    tax_amount: float = 0.0

    # Land characteristics
    land_use_current: str = ""
    soil_type: str = ""
    topography: str = ""
    avg_slope_pct: float = 0.0
    max_slope_pct: float = 0.0

    # Utilities
    road_access: bool = True
    road_frontage_ft: float = 0.0
    electric_on_site: bool = False
    water_on_site: bool = False

    # Scores (0-100)
    site_score: float = 0.0
    permitting_score: float = 0.0
    grid_score: float = 0.0
    environmental_score: float = 0.0

    # Metadata
    data_source: str = ""
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "apn": self.apn,
            "state": self.state,
            "county": self.county,
            "municipality": self.municipality,
            "acreage": self.acreage,
            "zoning_type": self.zoning_type.value,
            "solar_permission": self.solar_permission.value,
            "site_score": self.site_score,
            "permitting_score": self.permitting_score,
            "grid_score": self.grid_score,
            "environmental_score": self.environmental_score,
            "centroid": self.centroid.to_dict() if self.centroid else None,
        }


# =============================================================================
# Permitting Types
# =============================================================================

@dataclass
class Jurisdiction:
    """Authority Having Jurisdiction (AHJ) for permitting."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    type: str = ""  # county, city, township, etc.
    state: str = ""

    # Contact
    address: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""

    # Solar policy
    solar_ordinance_exists: bool = False
    ordinance_url: str = ""
    ordinance_text: str = ""

    # Permitting
    solar_permission: LandUsePermission = LandUsePermission.UNKNOWN
    permitted_zones: list[str] = field(default_factory=list)
    prohibited_zones: list[str] = field(default_factory=list)

    # Requirements
    setback_requirements: dict[str, float] = field(default_factory=dict)
    height_limit_ft: float = 0.0
    lot_coverage_max_pct: float = 0.0
    screening_required: bool = False
    decommissioning_required: bool = False

    # Process
    permit_types_required: list[str] = field(default_factory=list)
    public_hearing_required: bool = False
    avg_approval_days: int = 0

    # Scoring
    permitting_risk_score: float = 50.0  # 0-100, lower is better

    # Analysis
    ai_analysis: str = ""
    last_analyzed: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "state": self.state,
            "solar_permission": self.solar_permission.value,
            "permitting_risk_score": self.permitting_risk_score,
            "avg_approval_days": self.avg_approval_days,
            "public_hearing_required": self.public_hearing_required,
        }


@dataclass
class PermitApplication:
    """Permit application tracking."""
    id: str = field(default_factory=lambda: str(uuid4()))
    project_id: str = ""
    jurisdiction_id: str = ""

    permit_type: str = ""  # SUP, CUP, site plan, building, etc.
    status: PermitStatus = PermitStatus.NOT_STARTED

    # Timeline
    submitted_date: Optional[date] = None
    expected_decision_date: Optional[date] = None
    actual_decision_date: Optional[date] = None

    # Details
    conditions: list[str] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)
    fees_paid: float = 0.0

    notes: str = ""


# =============================================================================
# Grid / Interconnection Types
# =============================================================================

@dataclass
class Substation:
    """Electrical substation."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    utility: Utility = Utility.OTHER

    location: Optional[GeoPoint] = None
    voltage_kv: float = 0.0

    # Capacity
    total_capacity_mw: float = 0.0
    available_capacity_mw: float = 0.0
    queued_capacity_mw: float = 0.0

    # Status
    accepts_new_interconnections: bool = True
    upgrade_planned: bool = False
    upgrade_completion_date: Optional[date] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "utility": self.utility.value,
            "voltage_kv": self.voltage_kv,
            "available_capacity_mw": self.available_capacity_mw,
            "queued_capacity_mw": self.queued_capacity_mw,
            "location": self.location.to_dict() if self.location else None,
        }


@dataclass
class TransmissionLine:
    """Transmission or distribution line."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    utility: Utility = Utility.OTHER

    voltage_kv: float = 0.0
    line_type: str = ""  # transmission, distribution, feeder

    # Capacity
    thermal_rating_mw: float = 0.0
    available_capacity_mw: float = 0.0

    # Route
    start_point: Optional[GeoPoint] = None
    end_point: Optional[GeoPoint] = None
    length_miles: float = 0.0


@dataclass
class GridConnection:
    """Grid interconnection point analysis."""
    id: str = field(default_factory=lambda: str(uuid4()))
    parcel_id: str = ""

    # Nearest infrastructure
    nearest_substation_id: str = ""
    nearest_substation_name: str = ""
    distance_to_substation_miles: float = 0.0

    nearest_transmission_id: str = ""
    nearest_transmission_voltage_kv: float = 0.0
    distance_to_transmission_miles: float = 0.0

    nearest_distribution_id: str = ""
    distance_to_distribution_miles: float = 0.0

    # Capacity
    hosting_capacity_mw: float = 0.0
    available_capacity_mw: float = 0.0

    # Utility
    utility: Utility = Utility.OTHER
    iso_rto: str = ""  # ERCOT, PJM, MISO, etc.

    # Cost estimates
    estimated_interconnection_cost: float = 0.0
    estimated_upgrade_cost: float = 0.0
    estimated_total_cost: float = 0.0
    cost_per_mw: float = 0.0

    # Timeline
    estimated_study_months: int = 0
    estimated_construction_months: int = 0

    # Queue analysis
    queue_position: int = 0
    projects_ahead_in_queue: int = 0
    queue_mw_ahead: float = 0.0

    # Scoring
    grid_score: float = 50.0  # 0-100
    congestion_risk: str = "medium"  # low, medium, high

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "parcel_id": self.parcel_id,
            "distance_to_substation_miles": self.distance_to_substation_miles,
            "available_capacity_mw": self.available_capacity_mw,
            "estimated_interconnection_cost": self.estimated_interconnection_cost,
            "grid_score": self.grid_score,
            "utility": self.utility.value,
        }


@dataclass
class InterconnectionQueueEntry:
    """Entry in utility interconnection queue."""
    id: str = field(default_factory=lambda: str(uuid4()))
    queue_id: str = ""  # Utility's queue ID

    project_name: str = ""
    developer: str = ""
    project_type: ProjectType = ProjectType.UTILITY_SOLAR
    capacity_mw: float = 0.0

    # Location
    county: str = ""
    state: str = ""
    substation: str = ""

    # Status
    status: InterconnectionStatus = InterconnectionStatus.APPLICATION_SUBMITTED
    queue_date: Optional[date] = None

    # Studies
    feasibility_complete: bool = False
    system_impact_complete: bool = False
    facilities_study_complete: bool = False

    # Costs
    network_upgrade_cost: float = 0.0

    # Timeline
    expected_cod: Optional[date] = None

    utility: Utility = Utility.OTHER


# =============================================================================
# Environmental Types
# =============================================================================

@dataclass
class EnvironmentalConstraint:
    """Environmental constraint or sensitive area."""
    id: str = field(default_factory=lambda: str(uuid4()))
    parcel_id: str = ""

    constraint_type: str = ""  # wetland, flood_zone, endangered_species, etc.
    description: str = ""

    # Coverage
    affected_acreage: float = 0.0
    affected_percentage: float = 0.0

    # Risk
    risk_level: EnvironmentalRisk = EnvironmentalRisk.LOW
    is_fatal_flaw: bool = False

    # Mitigation
    mitigation_possible: bool = True
    estimated_mitigation_cost: float = 0.0
    mitigation_timeline_months: int = 0

    # Source
    data_source: str = ""
    regulation: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "constraint_type": self.constraint_type,
            "risk_level": self.risk_level.name,
            "affected_acreage": self.affected_acreage,
            "is_fatal_flaw": self.is_fatal_flaw,
        }


@dataclass
class EnvironmentalScreening:
    """Complete environmental screening for a parcel."""
    parcel_id: str = ""
    screening_date: datetime = field(default_factory=datetime.now)

    # Constraints found
    constraints: list[EnvironmentalConstraint] = field(default_factory=list)

    # Summary scores
    overall_risk: EnvironmentalRisk = EnvironmentalRisk.LOW
    environmental_score: float = 100.0  # 0-100

    # Specific checks
    wetlands_present: bool = False
    wetlands_acreage: float = 0.0

    flood_zone: str = ""  # X, A, AE, etc.
    flood_zone_acreage: float = 0.0

    endangered_species_habitat: bool = False
    species_of_concern: list[str] = field(default_factory=list)

    cultural_resources: bool = False
    historic_sites_nearby: bool = False

    prime_farmland: bool = False
    prime_farmland_acreage: float = 0.0

    # Recommendations
    recommended_studies: list[str] = field(default_factory=list)
    estimated_study_cost: float = 0.0

    # AI analysis
    ai_summary: str = ""

    def to_dict(self) -> dict:
        return {
            "parcel_id": self.parcel_id,
            "overall_risk": self.overall_risk.name,
            "environmental_score": self.environmental_score,
            "constraints_count": len(self.constraints),
            "wetlands_present": self.wetlands_present,
            "flood_zone": self.flood_zone,
            "endangered_species_habitat": self.endangered_species_habitat,
        }


# =============================================================================
# Solar Resource Types
# =============================================================================

@dataclass
class SolarResource:
    """Solar irradiance and resource data for a location."""
    location: Optional[GeoPoint] = None

    # Annual averages
    ghi_kwh_m2_day: float = 0.0  # Global Horizontal Irradiance
    dni_kwh_m2_day: float = 0.0  # Direct Normal Irradiance
    dhi_kwh_m2_day: float = 0.0  # Diffuse Horizontal Irradiance

    # Monthly GHI values
    monthly_ghi: list[float] = field(default_factory=list)

    # Capacity factor estimate
    capacity_factor_fixed: float = 0.0  # Fixed tilt
    capacity_factor_1axis: float = 0.0  # Single-axis tracking
    capacity_factor_2axis: float = 0.0  # Dual-axis tracking

    # Temperature
    avg_temperature_c: float = 0.0
    high_temperature_c: float = 0.0

    # Data source
    data_source: str = "NSRDB"  # NSRDB, PVGIS, etc.
    data_years: str = ""

    def to_dict(self) -> dict:
        return {
            "ghi_kwh_m2_day": self.ghi_kwh_m2_day,
            "dni_kwh_m2_day": self.dni_kwh_m2_day,
            "capacity_factor_1axis": self.capacity_factor_1axis,
            "data_source": self.data_source,
        }


# =============================================================================
# Financial Types
# =============================================================================

@dataclass
class ProjectFinancials:
    """Financial model for a renewable energy project."""
    project_id: str = ""

    # Project size
    capacity_mw_dc: float = 0.0
    capacity_mw_ac: float = 0.0

    # Capital costs
    module_cost: float = 0.0
    inverter_cost: float = 0.0
    bos_cost: float = 0.0  # Balance of system
    labor_cost: float = 0.0
    interconnection_cost: float = 0.0
    land_cost: float = 0.0
    permitting_cost: float = 0.0
    development_cost: float = 0.0
    contingency: float = 0.0
    total_capex: float = 0.0
    capex_per_watt: float = 0.0

    # Operating costs
    om_cost_annual: float = 0.0
    om_cost_per_kw: float = 0.0
    insurance_annual: float = 0.0
    land_lease_annual: float = 0.0
    property_tax_annual: float = 0.0
    total_opex_annual: float = 0.0

    # Revenue
    ppa_price_kwh: float = 0.0
    ppa_escalator_pct: float = 0.0
    ppa_term_years: int = 0

    # Production
    annual_production_mwh: float = 0.0
    degradation_rate_pct: float = 0.5

    # Returns
    npv: float = 0.0
    irr: float = 0.0
    payback_years: float = 0.0
    lcoe: float = 0.0  # Levelized cost of energy

    # Incentives
    itc_eligible: bool = True
    itc_rate: float = 0.30
    itc_value: float = 0.0
    depreciation_value: float = 0.0

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "capacity_mw_dc": self.capacity_mw_dc,
            "total_capex": self.total_capex,
            "capex_per_watt": self.capex_per_watt,
            "lcoe": self.lcoe,
            "npv": self.npv,
            "irr": self.irr,
            "payback_years": self.payback_years,
        }


# =============================================================================
# Site Scoring
# =============================================================================

@dataclass
class SiteScore:
    """Comprehensive site scoring for development viability."""
    parcel_id: str = ""
    scored_at: datetime = field(default_factory=datetime.now)

    # Component scores (0-100)
    overall_score: float = 0.0

    permitting_score: float = 0.0
    permitting_factors: dict[str, float] = field(default_factory=dict)

    grid_score: float = 0.0
    grid_factors: dict[str, float] = field(default_factory=dict)

    environmental_score: float = 0.0
    environmental_factors: dict[str, float] = field(default_factory=dict)

    land_score: float = 0.0
    land_factors: dict[str, float] = field(default_factory=dict)

    solar_resource_score: float = 0.0
    financial_score: float = 0.0

    # Risk assessment
    fatal_flaws: list[str] = field(default_factory=list)
    high_risks: list[str] = field(default_factory=list)
    medium_risks: list[str] = field(default_factory=list)

    # Recommendations
    proceed_recommendation: str = ""  # proceed, conditional, avoid
    key_actions: list[str] = field(default_factory=list)

    # AI analysis
    ai_summary: str = ""

    def to_dict(self) -> dict:
        return {
            "parcel_id": self.parcel_id,
            "overall_score": self.overall_score,
            "permitting_score": self.permitting_score,
            "grid_score": self.grid_score,
            "environmental_score": self.environmental_score,
            "land_score": self.land_score,
            "proceed_recommendation": self.proceed_recommendation,
            "fatal_flaws_count": len(self.fatal_flaws),
        }


# =============================================================================
# Project Types
# =============================================================================

@dataclass
class Project:
    """Renewable energy development project."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""

    # Type and status
    project_type: ProjectType = ProjectType.UTILITY_SOLAR
    status: ProjectStatus = ProjectStatus.PROSPECTING

    # Size
    capacity_mw_dc: float = 0.0
    capacity_mw_ac: float = 0.0
    storage_mwh: float = 0.0

    # Location
    parcel_ids: list[str] = field(default_factory=list)
    state: str = ""
    county: str = ""

    # Land
    total_acreage: float = 0.0
    lease_signed: bool = False
    lease_terms: str = ""

    # Permitting
    jurisdiction_id: str = ""
    permit_applications: list[str] = field(default_factory=list)
    permits_approved: bool = False

    # Interconnection
    interconnection_queue_id: str = ""
    interconnection_status: InterconnectionStatus = InterconnectionStatus.NOT_APPLIED
    utility: Utility = Utility.OTHER
    substation: str = ""

    # Timeline
    development_start: Optional[date] = None
    target_cod: Optional[date] = None
    actual_cod: Optional[date] = None

    # Financials
    estimated_capex: float = 0.0
    ppa_executed: bool = False
    ppa_price_kwh: float = 0.0
    offtaker: str = ""

    # Scoring
    site_score: float = 0.0

    # Team
    developer: str = ""
    owner: str = ""

    # Notes
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "project_type": self.project_type.value,
            "status": self.status.value,
            "capacity_mw_dc": self.capacity_mw_dc,
            "state": self.state,
            "county": self.county,
            "site_score": self.site_score,
            "target_cod": self.target_cod.isoformat() if self.target_cod else None,
        }


# =============================================================================
# Feasibility Report
# =============================================================================

@dataclass
class FeasibilityReport:
    """Complete feasibility assessment report."""
    id: str = field(default_factory=lambda: str(uuid4()))
    parcel_id: str = ""
    generated_at: datetime = field(default_factory=datetime.now)

    # Parcel summary
    parcel: Optional[Parcel] = None

    # Assessments
    site_score: Optional[SiteScore] = None
    grid_connection: Optional[GridConnection] = None
    environmental_screening: Optional[EnvironmentalScreening] = None
    solar_resource: Optional[SolarResource] = None
    financials: Optional[ProjectFinancials] = None
    jurisdiction: Optional[Jurisdiction] = None

    # Summary
    overall_viability: str = ""  # excellent, good, fair, poor, not_viable
    executive_summary: str = ""

    # Recommendations
    proceed_recommendation: str = ""
    key_risks: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    # Estimated project parameters
    recommended_capacity_mw: float = 0.0
    estimated_capex: float = 0.0
    estimated_lcoe: float = 0.0
    estimated_timeline_months: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "parcel_id": self.parcel_id,
            "generated_at": self.generated_at.isoformat(),
            "overall_viability": self.overall_viability,
            "recommended_capacity_mw": self.recommended_capacity_mw,
            "estimated_lcoe": self.estimated_lcoe,
            "proceed_recommendation": self.proceed_recommendation,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
