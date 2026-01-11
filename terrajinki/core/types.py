"""
TerraJinki Core Types

Comprehensive data models for renewable energy site development with
human-in-the-loop AI orchestration.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Callable, Awaitable
from uuid import uuid4
import json
import math


# =============================================================================
# ENUMERATIONS
# =============================================================================

class ProjectType(str, Enum):
    """Types of renewable energy projects."""
    UTILITY_SOLAR = "utility_solar"
    COMMUNITY_SOLAR = "community_solar"
    DISTRIBUTED_SOLAR = "distributed_solar"
    WIND_ONSHORE = "wind_onshore"
    WIND_OFFSHORE = "wind_offshore"
    BATTERY_STORAGE = "battery_storage"
    SOLAR_PLUS_STORAGE = "solar_plus_storage"
    HYDROGEN_GREEN = "hydrogen_green"
    DATA_CENTER = "data_center"
    EV_CHARGING = "ev_charging"
    HYBRID = "hybrid"


class ProjectStage(str, Enum):
    """Development pipeline stages."""
    PROSPECTING = "prospecting"
    DUE_DILIGENCE = "due_diligence"
    SITE_CONTROL = "site_control"
    PERMITTING = "permitting"
    INTERCONNECTION = "interconnection"
    FINANCING = "financing"
    CONSTRUCTION = "construction"
    OPERATIONS = "operations"
    DECOMMISSIONING = "decommissioning"


class ZoningType(str, Enum):
    """Zoning classifications."""
    AGRICULTURAL = "agricultural"
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    CONSERVATION = "conservation"
    PLANNED_DEVELOPMENT = "planned_development"
    UNZONED = "unzoned"


class SolarPermission(str, Enum):
    """Solar development permission levels."""
    BY_RIGHT = "by_right"  # Permitted without special approval
    CONDITIONAL_USE = "conditional_use"  # Requires CUP
    SPECIAL_EXCEPTION = "special_exception"  # Requires special exception
    VARIANCE_REQUIRED = "variance_required"  # Needs variance
    PROHIBITED = "prohibited"  # Not allowed
    MORATORIUM = "moratorium"  # Temporary ban
    UNDER_REVIEW = "under_review"  # Policy being revised
    UNKNOWN = "unknown"  # No clear guidance


class EnvironmentalRisk(str, Enum):
    """Environmental constraint severity levels."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    FATAL = "fatal"  # Project cannot proceed


class GridViability(str, Enum):
    """Grid connection viability assessment."""
    EXCELLENT = "excellent"  # < 1 mile to high-capacity POI
    GOOD = "good"  # 1-3 miles, adequate capacity
    MODERATE = "moderate"  # 3-5 miles or capacity constraints
    CHALLENGING = "challenging"  # 5-10 miles or major upgrades
    POOR = "poor"  # > 10 miles or no capacity
    FATAL = "fatal"  # No viable connection path


class ApprovalLevel(str, Enum):
    """Human approval requirement levels."""
    AUTONOMOUS = "autonomous"  # No human needed
    NOTIFY = "notify"  # Human notified, can override
    APPROVE = "approve"  # Human must approve
    COLLABORATE = "collaborate"  # Human works with AI


class AgentStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# GEOGRAPHIC TYPES
# =============================================================================

@dataclass
class GeoPoint:
    """Geographic point with latitude and longitude."""
    latitude: float
    longitude: float
    elevation_m: Optional[float] = None

    def distance_to(self, other: GeoPoint) -> float:
        """Calculate Haversine distance in miles."""
        R = 3959  # Earth radius in miles
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def to_geojson(self) -> Dict[str, Any]:
        """Convert to GeoJSON Point."""
        return {
            "type": "Point",
            "coordinates": [self.longitude, self.latitude]
        }


@dataclass
class GeoPolygon:
    """Geographic polygon defined by vertices."""
    vertices: List[GeoPoint]

    @property
    def centroid(self) -> GeoPoint:
        """Calculate polygon centroid."""
        if not self.vertices:
            raise ValueError("Polygon has no vertices")
        avg_lat = sum(v.latitude for v in self.vertices) / len(self.vertices)
        avg_lon = sum(v.longitude for v in self.vertices) / len(self.vertices)
        return GeoPoint(latitude=avg_lat, longitude=avg_lon)

    @property
    def area_acres(self) -> float:
        """Approximate area in acres using Shoelace formula."""
        if len(self.vertices) < 3:
            return 0.0

        # Simplified calculation - would use proper geodesic in production
        n = len(self.vertices)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += self.vertices[i].longitude * self.vertices[j].latitude
            area -= self.vertices[j].longitude * self.vertices[i].latitude

        area_sq_deg = abs(area) / 2.0
        # Approximate conversion (varies by latitude)
        area_sq_miles = area_sq_deg * 4761  # Approximate at mid-latitudes
        return area_sq_miles * 640  # Square miles to acres

    def to_geojson(self) -> Dict[str, Any]:
        """Convert to GeoJSON Polygon."""
        coords = [[v.longitude, v.latitude] for v in self.vertices]
        if coords and coords[0] != coords[-1]:
            coords.append(coords[0])  # Close the ring
        return {
            "type": "Polygon",
            "coordinates": [coords]
        }


@dataclass
class BoundingBox:
    """Geographic bounding box."""
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float

    def contains(self, point: GeoPoint) -> bool:
        """Check if point is within bounding box."""
        return (self.min_lat <= point.latitude <= self.max_lat and
                self.min_lon <= point.longitude <= self.max_lon)


# =============================================================================
# PARCEL & LAND TYPES
# =============================================================================

@dataclass
class Parcel:
    """
    Land parcel for renewable energy development analysis.
    Core entity that all analysis revolves around.
    """
    id: str = field(default_factory=lambda: str(uuid4()))

    # Identification
    apn: str = ""  # Assessor's Parcel Number
    legal_description: str = ""

    # Location
    state: str = ""
    county: str = ""
    municipality: str = ""
    address: str = ""
    centroid: Optional[GeoPoint] = None
    boundary: Optional[GeoPolygon] = None

    # Physical characteristics
    acreage: float = 0.0
    slope_avg_pct: float = 0.0
    slope_max_pct: float = 0.0
    elevation_min_ft: float = 0.0
    elevation_max_ft: float = 0.0
    aspect: str = ""  # N, NE, E, SE, S, SW, W, NW, FLAT

    # Zoning & Use
    zoning_type: ZoningType = ZoningType.AGRICULTURAL
    zoning_code: str = ""
    solar_permission: SolarPermission = SolarPermission.UNKNOWN
    current_use: str = ""

    # Ownership
    owner_name: str = ""
    owner_type: str = ""  # individual, corporation, trust, government
    owner_address: str = ""
    owner_phone: str = ""
    owner_email: str = ""

    # Valuation
    assessed_value: float = 0.0
    market_value: float = 0.0
    price_per_acre: float = 0.0
    last_sale_date: Optional[date] = None
    last_sale_price: float = 0.0

    # Utilities & Access
    road_access: bool = True
    road_frontage_ft: float = 0.0
    electric_available: bool = False
    water_available: bool = False
    nearest_substation_mi: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    data_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "apn": self.apn,
            "state": self.state,
            "county": self.county,
            "municipality": self.municipality,
            "address": self.address,
            "acreage": self.acreage,
            "zoning_type": self.zoning_type.value,
            "solar_permission": self.solar_permission.value,
            "centroid": self.centroid.to_geojson() if self.centroid else None,
        }


@dataclass
class LandOwner:
    """Landowner information for outreach."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    entity_type: str = ""  # individual, llc, corporation, trust
    address: str = ""
    phone: str = ""
    email: str = ""
    total_acreage: float = 0.0
    parcel_count: int = 0
    parcel_ids: List[str] = field(default_factory=list)
    contact_history: List[Dict[str, Any]] = field(default_factory=list)
    interest_level: str = ""  # not_contacted, interested, negotiating, declined


# =============================================================================
# JURISDICTION & PERMITTING TYPES
# =============================================================================

@dataclass
class Jurisdiction:
    """Authority Having Jurisdiction (AHJ) for permitting."""
    id: str = field(default_factory=lambda: str(uuid4()))

    # Identification
    name: str = ""
    type: str = ""  # county, municipality, township
    state: str = ""
    fips_code: str = ""

    # Solar policy
    solar_ordinance_exists: bool = False
    solar_ordinance_url: str = ""
    solar_ordinance_text: str = ""
    solar_ordinance_updated: Optional[date] = None

    # Permissions
    utility_solar_permission: SolarPermission = SolarPermission.UNKNOWN
    community_solar_permission: SolarPermission = SolarPermission.UNKNOWN
    battery_storage_permission: SolarPermission = SolarPermission.UNKNOWN

    # Requirements
    setback_requirements: Dict[str, float] = field(default_factory=dict)
    height_limit_ft: float = 0.0
    lot_coverage_max_pct: float = 0.0
    screening_required: bool = False
    decommissioning_bond_required: bool = False

    # Historical data
    permits_approved_last_year: int = 0
    permits_denied_last_year: int = 0
    avg_approval_days: float = 0.0

    # Analysis
    permitting_risk_score: float = 0.0  # 0-100
    confidence: float = 0.0  # 0-1
    last_analyzed: Optional[datetime] = None


@dataclass
class PermitApplication:
    """Permit application tracking."""
    id: str = field(default_factory=lambda: str(uuid4()))
    project_id: str = ""
    jurisdiction_id: str = ""

    permit_type: str = ""  # conditional_use, building, electrical, etc.
    status: str = ""  # draft, submitted, under_review, approved, denied

    submitted_date: Optional[date] = None
    expected_decision_date: Optional[date] = None
    actual_decision_date: Optional[date] = None

    conditions: List[str] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)
    fees_paid: float = 0.0

    notes: str = ""


# =============================================================================
# GRID & INTERCONNECTION TYPES
# =============================================================================

@dataclass
class Substation:
    """Electrical substation for interconnection."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    utility: str = ""
    location: Optional[GeoPoint] = None

    voltage_kv: float = 0.0
    capacity_mw: float = 0.0
    available_capacity_mw: float = 0.0

    interconnection_queue_count: int = 0
    avg_interconnection_cost_per_mw: float = 0.0

    upgrade_needed: bool = False
    upgrade_cost_estimate: float = 0.0
    upgrade_timeline_months: int = 0


@dataclass
class TransmissionLine:
    """Transmission line infrastructure."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    utility: str = ""

    voltage_kv: float = 0.0
    capacity_mw: float = 0.0
    length_miles: float = 0.0

    start_substation_id: str = ""
    end_substation_id: str = ""

    congestion_level: str = ""  # low, moderate, high, critical


@dataclass
class GridAnalysis:
    """Grid interconnection analysis results."""
    id: str = field(default_factory=lambda: str(uuid4()))
    parcel_id: str = ""
    analyzed_at: datetime = field(default_factory=datetime.utcnow)

    # Nearest infrastructure
    nearest_substation: Optional[Substation] = None
    distance_to_substation_mi: float = 0.0
    nearest_transmission_line_mi: float = 0.0

    # Capacity analysis
    available_capacity_mw: float = 0.0
    recommended_project_size_mw: float = 0.0
    hosting_capacity_limited: bool = False

    # Queue analysis
    queue_position: int = 0
    projects_ahead_mw: float = 0.0
    estimated_study_completion: Optional[date] = None
    withdrawal_risk_pct: float = 0.0

    # Cost estimates
    gen_tie_cost: float = 0.0
    interconnection_study_cost: float = 0.0
    network_upgrade_cost: float = 0.0
    total_interconnection_cost: float = 0.0
    cost_per_mw: float = 0.0

    # Timeline
    estimated_months_to_IA: int = 0
    estimated_months_to_COD: int = 0

    # Risk assessment
    grid_viability: GridViability = GridViability.MODERATE
    grid_score: float = 0.0  # 0-100
    risks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # GNN model outputs (if available)
    gnn_topology_score: float = 0.0
    gnn_congestion_prediction: float = 0.0
    gnn_upgrade_probability: float = 0.0


# =============================================================================
# ENVIRONMENTAL TYPES
# =============================================================================

@dataclass
class EnvironmentalConstraint:
    """Environmental constraint or sensitive area."""
    id: str = field(default_factory=lambda: str(uuid4()))

    constraint_type: str = ""  # wetland, flood_zone, endangered_species, etc.
    description: str = ""
    data_source: str = ""

    risk_level: EnvironmentalRisk = EnvironmentalRisk.LOW
    affected_area_acres: float = 0.0
    affected_area_pct: float = 0.0

    mitigation_possible: bool = True
    mitigation_cost_estimate: float = 0.0
    mitigation_timeline_months: int = 0

    required_studies: List[str] = field(default_factory=list)
    required_permits: List[str] = field(default_factory=list)

    regulatory_agency: str = ""
    consultation_required: bool = False


@dataclass
class EnvironmentalScreening:
    """Environmental screening results for a parcel."""
    id: str = field(default_factory=lambda: str(uuid4()))
    parcel_id: str = ""
    screened_at: datetime = field(default_factory=datetime.utcnow)

    # Constraint findings
    constraints: List[EnvironmentalConstraint] = field(default_factory=list)

    # Wetlands
    wetlands_present: bool = False
    wetlands_acres: float = 0.0
    wetlands_type: str = ""  # emergent, forested, scrub-shrub
    section_404_required: bool = False

    # Flood zones
    flood_zone: str = ""  # X, A, AE, VE
    flood_zone_acres: float = 0.0
    flood_insurance_required: bool = False

    # Species
    threatened_species: List[str] = field(default_factory=list)
    endangered_species: List[str] = field(default_factory=list)
    critical_habitat_present: bool = False
    esa_consultation_required: bool = False

    # Other
    cultural_resources_risk: str = ""  # low, moderate, high
    prime_farmland: bool = False
    prime_farmland_acres: float = 0.0

    # Satellite analysis
    satellite_land_cover: str = ""
    satellite_confidence: float = 0.0
    satellite_imagery_date: Optional[date] = None

    # Overall assessment
    environmental_risk: EnvironmentalRisk = EnvironmentalRisk.LOW
    environmental_score: float = 0.0  # 0-100
    buildable_area_acres: float = 0.0

    required_studies: List[str] = field(default_factory=list)
    estimated_study_cost: float = 0.0
    estimated_study_months: int = 0

    recommendations: List[str] = field(default_factory=list)


# =============================================================================
# SOLAR RESOURCE TYPES
# =============================================================================

@dataclass
class SolarResource:
    """Solar resource assessment for a location."""
    id: str = field(default_factory=lambda: str(uuid4()))
    location: Optional[GeoPoint] = None
    assessed_at: datetime = field(default_factory=datetime.utcnow)

    # Irradiance data
    ghi_kwh_m2_day: float = 0.0  # Global Horizontal Irradiance
    dni_kwh_m2_day: float = 0.0  # Direct Normal Irradiance
    dhi_kwh_m2_day: float = 0.0  # Diffuse Horizontal Irradiance

    # Monthly breakdown
    monthly_ghi: List[float] = field(default_factory=list)  # 12 values
    monthly_dni: List[float] = field(default_factory=list)

    # Performance estimates
    capacity_factor_pct: float = 0.0
    specific_yield_kwh_kwp: float = 0.0
    annual_production_mwh_per_mw: float = 0.0

    # Losses
    soiling_loss_pct: float = 2.0
    snow_loss_pct: float = 0.0
    shading_loss_pct: float = 0.0
    temperature_loss_pct: float = 0.0

    # Confidence
    data_source: str = ""  # NSRDB, PVGIS, SolarAnywhere
    data_years: int = 0
    p50_confidence: float = 0.0
    p90_confidence: float = 0.0


# =============================================================================
# FINANCIAL TYPES
# =============================================================================

@dataclass
class FinancialAssumptions:
    """Financial modeling assumptions."""
    # Project parameters
    project_size_mw: float = 0.0
    project_type: ProjectType = ProjectType.UTILITY_SOLAR

    # CAPEX
    module_cost_per_w: float = 0.25
    inverter_cost_per_w: float = 0.05
    racking_cost_per_w: float = 0.10
    bos_cost_per_w: float = 0.15
    installation_cost_per_w: float = 0.10
    soft_costs_per_w: float = 0.15
    contingency_pct: float = 10.0

    # OPEX
    om_cost_per_kw_year: float = 15.0
    insurance_pct_of_capex: float = 0.25
    land_lease_per_acre_year: float = 1000.0
    property_tax_pct: float = 1.0

    # Revenue
    ppa_price_per_mwh: float = 40.0
    ppa_escalation_pct: float = 1.5
    ppa_term_years: int = 20
    merchant_price_per_mwh: float = 35.0

    # Tax
    itc_pct: float = 30.0
    itc_adders_pct: float = 10.0  # Domestic content, energy community
    depreciation_schedule: str = "MACRS_5"
    federal_tax_rate: float = 21.0
    state_tax_rate: float = 5.0

    # Financing
    debt_pct: float = 70.0
    debt_interest_rate: float = 6.0
    debt_term_years: int = 18
    dscr_min: float = 1.30

    # Other
    project_life_years: int = 35
    degradation_pct_year: float = 0.5
    discount_rate: float = 8.0


@dataclass
class ProjectFinancials:
    """Complete financial analysis results."""
    id: str = field(default_factory=lambda: str(uuid4()))
    parcel_id: str = ""
    project_id: str = ""
    analyzed_at: datetime = field(default_factory=datetime.utcnow)

    assumptions: Optional[FinancialAssumptions] = None

    # Project sizing
    capacity_mw_dc: float = 0.0
    capacity_mw_ac: float = 0.0
    dc_ac_ratio: float = 1.3

    # CAPEX breakdown
    module_cost: float = 0.0
    inverter_cost: float = 0.0
    racking_cost: float = 0.0
    bos_cost: float = 0.0
    installation_cost: float = 0.0
    soft_costs: float = 0.0
    interconnection_cost: float = 0.0
    land_cost: float = 0.0
    contingency: float = 0.0
    total_capex: float = 0.0
    capex_per_w: float = 0.0

    # Annual values
    annual_production_mwh: float = 0.0
    annual_revenue_year1: float = 0.0
    annual_opex_year1: float = 0.0
    annual_ebitda_year1: float = 0.0

    # Returns
    npv: float = 0.0
    irr_unlevered: float = 0.0
    irr_levered: float = 0.0
    lcoe: float = 0.0  # $/MWh
    payback_years: float = 0.0

    # Debt sizing
    debt_capacity: float = 0.0
    annual_debt_service: float = 0.0
    dscr_min: float = 0.0

    # Tax benefits
    itc_value: float = 0.0
    depreciation_value: float = 0.0

    # Sensitivity
    min_viable_ppa: float = 0.0  # Minimum PPA for target IRR
    breakeven_capex: float = 0.0

    # Risk metrics
    financial_risk_score: float = 0.0  # 0-100


# =============================================================================
# SITE ANALYSIS & SCORING TYPES
# =============================================================================

@dataclass
class SiteScore:
    """Comprehensive site scoring across all dimensions."""
    parcel_id: str = ""
    scored_at: datetime = field(default_factory=datetime.utcnow)

    # Component scores (0-100)
    permitting_score: float = 0.0
    grid_score: float = 0.0
    environmental_score: float = 0.0
    land_score: float = 0.0
    financial_score: float = 0.0

    # Weights (must sum to 1.0)
    permitting_weight: float = 0.30
    grid_weight: float = 0.30
    environmental_weight: float = 0.20
    land_weight: float = 0.10
    financial_weight: float = 0.10

    # Overall
    overall_score: float = 0.0
    star_rating: int = 0  # 1-5 stars
    viability: str = ""  # excellent, good, moderate, challenging, poor, fatal

    # Risks
    fatal_flaws: List[str] = field(default_factory=list)
    major_risks: List[str] = field(default_factory=list)
    minor_risks: List[str] = field(default_factory=list)

    # Opportunities
    opportunities: List[str] = field(default_factory=list)

    # Confidence
    confidence: float = 0.0  # 0-1
    data_completeness: float = 0.0  # 0-1

    def calculate_overall(self) -> float:
        """Calculate weighted overall score."""
        self.overall_score = (
            self.permitting_score * self.permitting_weight +
            self.grid_score * self.grid_weight +
            self.environmental_score * self.environmental_weight +
            self.land_score * self.land_weight +
            self.financial_score * self.financial_weight
        )

        # Determine star rating
        if self.overall_score >= 90:
            self.star_rating = 5
            self.viability = "excellent"
        elif self.overall_score >= 75:
            self.star_rating = 4
            self.viability = "good"
        elif self.overall_score >= 60:
            self.star_rating = 3
            self.viability = "moderate"
        elif self.overall_score >= 40:
            self.star_rating = 2
            self.viability = "challenging"
        elif self.overall_score >= 20:
            self.star_rating = 1
            self.viability = "poor"
        else:
            self.star_rating = 0
            self.viability = "fatal"

        return self.overall_score


@dataclass
class SiteAnalysis:
    """Complete site analysis combining all agent results."""
    id: str = field(default_factory=lambda: str(uuid4()))
    parcel_id: str = ""
    project_type: ProjectType = ProjectType.UTILITY_SOLAR

    requested_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Component analyses
    permitting: Optional[Jurisdiction] = None
    grid: Optional[GridAnalysis] = None
    environmental: Optional[EnvironmentalScreening] = None
    solar_resource: Optional[SolarResource] = None
    financials: Optional[ProjectFinancials] = None

    # Overall
    score: Optional[SiteScore] = None

    # Recommendations
    proceed_recommendation: str = ""  # proceed, proceed_with_caution, do_not_proceed
    recommended_next_steps: List[str] = field(default_factory=list)
    estimated_development_cost: float = 0.0
    estimated_development_months: int = 0

    # Agent tracking
    agents_executed: List[str] = field(default_factory=list)
    agent_durations: Dict[str, float] = field(default_factory=dict)

    # Human oversight
    requires_human_review: bool = False
    review_reasons: List[str] = field(default_factory=list)
    human_decision: Optional[HumanDecision] = None


# =============================================================================
# HUMAN-IN-THE-LOOP TYPES
# =============================================================================

@dataclass
class ApprovalGate:
    """Human approval gate configuration."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""

    level: ApprovalLevel = ApprovalLevel.NOTIFY

    # Trigger conditions
    trigger_conditions: List[str] = field(default_factory=list)
    score_threshold: Optional[float] = None
    cost_threshold: Optional[float] = None

    # Notification
    notify_users: List[str] = field(default_factory=list)
    notify_channels: List[str] = field(default_factory=list)  # email, slack, sms

    # Timeout
    timeout_hours: float = 24.0
    timeout_action: str = "escalate"  # escalate, approve, deny, skip


@dataclass
class HumanDecision:
    """Record of human decision on an approval gate."""
    id: str = field(default_factory=lambda: str(uuid4()))
    gate_id: str = ""
    analysis_id: str = ""

    decision: str = ""  # approved, denied, modified, deferred
    decided_by: str = ""
    decided_at: datetime = field(default_factory=datetime.utcnow)

    reasoning: str = ""
    modifications: Dict[str, Any] = field(default_factory=dict)

    # Audit
    time_to_decision_hours: float = 0.0


# =============================================================================
# PROJECT & PIPELINE TYPES
# =============================================================================

@dataclass
class Project:
    """Development project tracking."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""

    # Classification
    project_type: ProjectType = ProjectType.UTILITY_SOLAR
    stage: ProjectStage = ProjectStage.PROSPECTING

    # Parcels
    parcel_ids: List[str] = field(default_factory=list)
    total_acreage: float = 0.0

    # Sizing
    capacity_mw: float = 0.0
    storage_mwh: float = 0.0

    # Location
    state: str = ""
    county: str = ""
    utility: str = ""
    iso_rto: str = ""  # ERCOT, PJM, CAISO, etc.

    # Timeline
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    target_cod: Optional[date] = None

    # Team
    owner_id: str = ""
    team_members: List[str] = field(default_factory=list)

    # Analyses
    site_analyses: List[str] = field(default_factory=list)
    latest_score: float = 0.0

    # Documents
    documents: List[str] = field(default_factory=list)

    # Status
    is_active: bool = True
    notes: str = ""
    tags: List[str] = field(default_factory=list)


# =============================================================================
# AGENT RESULT TYPES
# =============================================================================

@dataclass
class AgentResult:
    """Result from an AI agent execution."""
    agent_id: str = ""
    agent_type: str = ""

    status: AgentStatus = AgentStatus.COMPLETED
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Results
    success: bool = True
    output: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    confidence: float = 0.0

    # Errors
    error_message: str = ""
    error_details: Dict[str, Any] = field(default_factory=dict)

    # LLM usage
    model_used: str = ""
    tokens_input: int = 0
    tokens_output: int = 0
    llm_cost: float = 0.0

    # Human oversight
    requires_approval: bool = False
    approval_reason: str = ""
    approval_gate: Optional[ApprovalGate] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SwarmResult:
    """Result from a swarm of agents."""
    swarm_id: str = ""
    swarm_type: str = ""  # permitting, grid, environmental, land

    status: AgentStatus = AgentStatus.COMPLETED
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Component results
    agent_results: List[AgentResult] = field(default_factory=list)

    # Aggregated
    overall_score: float = 0.0
    confidence: float = 0.0

    # Summary
    key_findings: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Costs
    total_tokens: int = 0
    total_cost: float = 0.0

    # Human oversight
    requires_approval: bool = False
    approval_reasons: List[str] = field(default_factory=list)


# =============================================================================
# SEARCH & FILTER TYPES
# =============================================================================

@dataclass
class ParcelSearchQuery:
    """Natural language or structured parcel search."""
    # Natural language
    query: str = ""

    # Structured filters
    states: List[str] = field(default_factory=list)
    counties: List[str] = field(default_factory=list)

    min_acreage: float = 0.0
    max_acreage: float = float('inf')

    zoning_types: List[ZoningType] = field(default_factory=list)
    solar_permissions: List[SolarPermission] = field(default_factory=list)

    max_distance_to_substation_mi: float = float('inf')
    min_available_capacity_mw: float = 0.0

    exclude_wetlands: bool = False
    exclude_flood_zones: bool = False
    exclude_endangered_species: bool = False

    min_score: float = 0.0

    # Spatial
    bounding_box: Optional[BoundingBox] = None
    near_point: Optional[GeoPoint] = None
    near_point_radius_mi: float = 0.0

    # Pagination
    limit: int = 100
    offset: int = 0

    # Sorting
    sort_by: str = "score"  # score, acreage, distance, price
    sort_order: str = "desc"


@dataclass
class SearchResult:
    """Search result with matched parcels."""
    query: Optional[ParcelSearchQuery] = None

    total_matches: int = 0
    returned_count: int = 0

    parcels: List[Parcel] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)

    # AI interpretation
    interpreted_query: str = ""
    suggestions: List[str] = field(default_factory=list)

    # Performance
    search_duration_ms: float = 0.0


# =============================================================================
# UTILITY TYPES
# =============================================================================

@dataclass
class DataSource:
    """External data source configuration."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    type: str = ""  # parcel, grid, environmental, solar, ordinance

    provider: str = ""
    api_url: str = ""
    api_key_env: str = ""  # Environment variable name

    refresh_frequency: str = ""  # hourly, daily, weekly, monthly
    last_refresh: Optional[datetime] = None

    is_active: bool = True
    priority: int = 0  # Lower = higher priority


@dataclass
class Notification:
    """User notification."""
    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""

    type: str = ""  # alert, info, approval_required, analysis_complete
    title: str = ""
    message: str = ""

    related_entity_type: str = ""  # parcel, project, analysis
    related_entity_id: str = ""

    created_at: datetime = field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None

    action_url: str = ""
    action_label: str = ""


# =============================================================================
# TYPE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ProjectType",
    "ProjectStage",
    "ZoningType",
    "SolarPermission",
    "EnvironmentalRisk",
    "GridViability",
    "ApprovalLevel",
    "AgentStatus",

    # Geographic
    "GeoPoint",
    "GeoPolygon",
    "BoundingBox",

    # Land
    "Parcel",
    "LandOwner",

    # Permitting
    "Jurisdiction",
    "PermitApplication",

    # Grid
    "Substation",
    "TransmissionLine",
    "GridAnalysis",

    # Environmental
    "EnvironmentalConstraint",
    "EnvironmentalScreening",

    # Solar
    "SolarResource",

    # Financial
    "FinancialAssumptions",
    "ProjectFinancials",

    # Scoring
    "SiteScore",
    "SiteAnalysis",

    # Human-in-the-loop
    "ApprovalGate",
    "HumanDecision",

    # Project
    "Project",

    # Agent
    "AgentResult",
    "SwarmResult",

    # Search
    "ParcelSearchQuery",
    "SearchResult",

    # Utility
    "DataSource",
    "Notification",
]
