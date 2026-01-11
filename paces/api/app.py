"""
Paces REST API - FastAPI application for renewable energy site development.

Endpoints:
- /parcels - Parcel search and management
- /sites - Site analysis
- /permitting - Permitting analysis
- /grid - Grid interconnection analysis
- /environmental - Environmental screening
- /financial - Financial modeling
- /projects - Project pipeline management
- /reports - Report generation
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger

from paces import __version__
from paces.core.config import PacesConfig, load_config
from paces.core.engine import PacesEngine
from paces.core.types import (
    Parcel,
    Project,
    Jurisdiction,
    GeoPoint,
    ZoningType,
    LandUsePermission,
    ProjectType,
    ProjectStatus,
)
from paces.financial.analyzer import FinancialAssumptions


# =============================================================================
# Pydantic Models for API
# =============================================================================

class ParcelCreate(BaseModel):
    """Request model for creating a parcel."""
    apn: str = ""
    state: str
    county: str
    municipality: str = ""
    address: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    acreage: float
    zoning_code: str = ""
    zoning_type: str = "unknown"
    owner_name: str = ""


class ParcelResponse(BaseModel):
    """Response model for parcel."""
    id: str
    apn: str
    state: str
    county: str
    municipality: str
    acreage: float
    zoning_type: str
    solar_permission: str
    site_score: float
    permitting_score: float
    grid_score: float
    environmental_score: float


class SiteAnalysisRequest(BaseModel):
    """Request model for site analysis."""
    parcel_id: str
    project_type: str = "utility_solar"
    target_capacity_mw: float = 5.0


class SiteAnalysisResponse(BaseModel):
    """Response model for site analysis."""
    parcel_id: str
    overall_score: float
    permitting_score: float
    grid_score: float
    environmental_score: float
    land_score: float
    proceed_recommendation: str
    overall_viability: str
    risks: List[str]
    recommendations: List[str]
    executive_summary: str


class PermittingRequest(BaseModel):
    """Request for permitting analysis."""
    parcel_id: str
    ordinance_text: Optional[str] = None
    capacity_mw: float = 5.0


class GridAnalysisRequest(BaseModel):
    """Request for grid analysis."""
    parcel_id: str
    capacity_mw: float = 5.0


class EnvironmentalRequest(BaseModel):
    """Request for environmental screening."""
    parcel_id: str
    detailed: bool = False


class FinancialRequest(BaseModel):
    """Request for financial analysis."""
    parcel_id: str
    capacity_mw_dc: float = 5.0
    ppa_price_kwh: float = 0.035
    itc_rate: float = 0.30


class ProjectCreate(BaseModel):
    """Request for creating a project."""
    name: str
    parcel_ids: List[str]
    project_type: str = "utility_solar"
    capacity_mw: float = 5.0


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str


# =============================================================================
# FastAPI Application
# =============================================================================

def create_app(config: PacesConfig = None) -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title="Paces API",
        description="AI-Powered Renewable Energy Site Development Platform",
        version=__version__,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Engine instance
    engine: Optional[PacesEngine] = None

    @app.on_event("startup")
    async def startup():
        nonlocal engine
        cfg = config or load_config()
        engine = PacesEngine(cfg)
        await engine.initialize()
        logger.info("Paces API started")

    @app.on_event("shutdown")
    async def shutdown():
        if engine:
            await engine.shutdown()
        logger.info("Paces API shutdown")

    # =========================================================================
    # Health & Info
    # =========================================================================

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            version=__version__,
            timestamp=datetime.now().isoformat(),
        )

    @app.get("/stats")
    async def get_stats():
        """Get engine statistics."""
        return engine.get_stats() if engine else {}

    # =========================================================================
    # Parcels
    # =========================================================================

    @app.post("/parcels", response_model=ParcelResponse)
    async def create_parcel(data: ParcelCreate):
        """Create a new parcel."""
        parcel = Parcel(
            apn=data.apn,
            state=data.state,
            county=data.county,
            municipality=data.municipality,
            address=data.address,
            acreage=data.acreage,
            zoning_code=data.zoning_code,
            zoning_type=ZoningType(data.zoning_type) if data.zoning_type in [z.value for z in ZoningType] else ZoningType.UNKNOWN,
            owner_name=data.owner_name,
            centroid=GeoPoint(data.latitude, data.longitude) if data.latitude and data.longitude else None,
        )
        engine.add_parcel(parcel)
        return _parcel_to_response(parcel)

    @app.get("/parcels", response_model=List[ParcelResponse])
    async def search_parcels(
        state: Optional[str] = None,
        county: Optional[str] = None,
        min_acreage: Optional[float] = None,
        max_acreage: Optional[float] = None,
        limit: int = Query(default=100, le=1000),
    ):
        """Search for parcels."""
        parcels = await engine.search_parcels(
            state=state,
            county=county,
            min_acreage=min_acreage,
            max_acreage=max_acreage,
            limit=limit,
        )
        return [_parcel_to_response(p) for p in parcels]

    @app.get("/parcels/{parcel_id}", response_model=ParcelResponse)
    async def get_parcel(parcel_id: str):
        """Get a parcel by ID."""
        parcel = engine.get_parcel(parcel_id)
        if not parcel:
            raise HTTPException(status_code=404, detail="Parcel not found")
        return _parcel_to_response(parcel)

    def _parcel_to_response(parcel: Parcel) -> ParcelResponse:
        return ParcelResponse(
            id=parcel.id,
            apn=parcel.apn,
            state=parcel.state,
            county=parcel.county,
            municipality=parcel.municipality,
            acreage=parcel.acreage,
            zoning_type=parcel.zoning_type.value,
            solar_permission=parcel.solar_permission.value,
            site_score=parcel.site_score,
            permitting_score=parcel.permitting_score,
            grid_score=parcel.grid_score,
            environmental_score=parcel.environmental_score,
        )

    # =========================================================================
    # Site Analysis
    # =========================================================================

    @app.post("/sites/analyze", response_model=SiteAnalysisResponse)
    async def analyze_site(request: SiteAnalysisRequest):
        """Perform comprehensive site analysis."""
        parcel = engine.get_parcel(request.parcel_id)
        if not parcel:
            raise HTTPException(status_code=404, detail="Parcel not found")

        project_type = ProjectType(request.project_type) if request.project_type in [p.value for p in ProjectType] else ProjectType.UTILITY_SOLAR

        report = await engine.analyze_site(
            parcel=parcel,
            project_type=project_type,
            target_capacity_mw=request.target_capacity_mw,
        )

        if not report:
            raise HTTPException(status_code=500, detail="Analysis failed")

        score = report.site_score

        return SiteAnalysisResponse(
            parcel_id=report.parcel_id,
            overall_score=score.overall_score if score else 0,
            permitting_score=score.permitting_score if score else 0,
            grid_score=score.grid_score if score else 0,
            environmental_score=score.environmental_score if score else 0,
            land_score=score.land_score if score else 0,
            proceed_recommendation=report.proceed_recommendation,
            overall_viability=report.overall_viability,
            risks=report.key_risks,
            recommendations=report.next_steps,
            executive_summary=report.executive_summary,
        )

    @app.post("/sites/analyze-batch")
    async def analyze_sites_batch(parcel_ids: List[str], capacity_mw: float = 5.0):
        """Analyze multiple sites and rank them."""
        parcels = [engine.get_parcel(pid) for pid in parcel_ids]
        parcels = [p for p in parcels if p is not None]

        if not parcels:
            raise HTTPException(status_code=404, detail="No valid parcels found")

        reports = await engine.analyze_multiple_sites(
            parcels=parcels,
            target_capacity_mw=capacity_mw,
        )

        return [
            {
                "parcel_id": r.parcel_id,
                "overall_score": r.site_score.overall_score if r.site_score else 0,
                "viability": r.overall_viability,
                "recommendation": r.proceed_recommendation,
            }
            for r in reports
        ]

    # =========================================================================
    # Permitting
    # =========================================================================

    @app.post("/permitting/analyze")
    async def analyze_permitting(request: PermittingRequest):
        """Analyze permitting requirements for a parcel."""
        parcel = engine.get_parcel(request.parcel_id)
        if not parcel:
            raise HTTPException(status_code=404, detail="Parcel not found")

        result = await engine.analyze_permitting(
            parcel=parcel,
            ordinance_text=request.ordinance_text,
            capacity_mw=request.capacity_mw,
        )

        return result

    # =========================================================================
    # Grid
    # =========================================================================

    @app.post("/grid/analyze")
    async def analyze_grid(request: GridAnalysisRequest):
        """Analyze grid interconnection for a parcel."""
        parcel = engine.get_parcel(request.parcel_id)
        if not parcel:
            raise HTTPException(status_code=404, detail="Parcel not found")

        result = await engine.analyze_grid(
            parcel=parcel,
            capacity_mw=request.capacity_mw,
        )

        return result

    # =========================================================================
    # Environmental
    # =========================================================================

    @app.post("/environmental/screen")
    async def screen_environmental(request: EnvironmentalRequest):
        """Screen parcel for environmental constraints."""
        parcel = engine.get_parcel(request.parcel_id)
        if not parcel:
            raise HTTPException(status_code=404, detail="Parcel not found")

        result = await engine.screen_environmental(
            parcel=parcel,
            detailed=request.detailed,
        )

        return result

    # =========================================================================
    # Financial
    # =========================================================================

    @app.post("/financial/analyze")
    async def analyze_financials(request: FinancialRequest):
        """Perform financial analysis for a solar project."""
        parcel = engine.get_parcel(request.parcel_id)
        if not parcel:
            raise HTTPException(status_code=404, detail="Parcel not found")

        assumptions = FinancialAssumptions(
            capacity_mw_dc=request.capacity_mw_dc,
            ppa_price_kwh=request.ppa_price_kwh,
            itc_rate=request.itc_rate,
        )

        result = engine.analyze_financials(
            parcel=parcel,
            assumptions=assumptions,
        )

        return result

    @app.post("/financial/min-ppa")
    async def calculate_min_ppa(parcel_id: str, target_irr: float = 0.10):
        """Calculate minimum PPA price for target IRR."""
        parcel = engine.get_parcel(parcel_id)
        if not parcel:
            raise HTTPException(status_code=404, detail="Parcel not found")

        min_ppa = engine.calculate_min_ppa(parcel=parcel, target_irr=target_irr)

        return {"min_ppa_price_kwh": min_ppa, "target_irr": target_irr}

    # =========================================================================
    # Projects
    # =========================================================================

    @app.post("/projects")
    async def create_project(request: ProjectCreate):
        """Create a new project."""
        project_type = ProjectType(request.project_type) if request.project_type in [p.value for p in ProjectType] else ProjectType.UTILITY_SOLAR

        project = engine.create_project(
            name=request.name,
            parcel_ids=request.parcel_ids,
            project_type=project_type,
            capacity_mw=request.capacity_mw,
        )

        return project.to_dict()

    @app.get("/projects")
    async def list_projects():
        """List all projects."""
        projects = engine.list_projects()
        return [p.to_dict() for p in projects]

    @app.get("/projects/{project_id}")
    async def get_project(project_id: str):
        """Get a project by ID."""
        project = engine.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project.to_dict()

    # =========================================================================
    # Reports
    # =========================================================================

    @app.post("/reports/feasibility")
    async def generate_feasibility_report(parcel_id: str, format: str = "markdown"):
        """Generate feasibility report for a parcel."""
        parcel = engine.get_parcel(parcel_id)
        if not parcel:
            raise HTTPException(status_code=404, detail="Parcel not found")

        # Run analysis first
        report = await engine.analyze_site(parcel=parcel)
        if not report:
            raise HTTPException(status_code=500, detail="Analysis failed")

        # Generate report
        content = await engine.generate_report(report, format=format)

        return {"format": format, "content": content}

    return app


# Create default app instance
app = create_app()
