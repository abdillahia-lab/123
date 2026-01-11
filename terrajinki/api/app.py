"""
TerraJinki API

FastAPI application with REST endpoints and WebSocket support
for real-time analysis streaming.
"""

from __future__ import annotations
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Dict, List, Any
from uuid import uuid4
import asyncio
import json
import logging

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from terrajinki.core.config import get_config, TerraJinkiConfig
from terrajinki.core.engine import TerraJinkiEngine
from terrajinki.core.types import (
    Parcel,
    Project,
    SiteAnalysis,
    ProjectType,
    ProjectStage,
    ZoningType,
    SolarPermission,
    GeoPoint,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: str


class StatsResponse(BaseModel):
    """Engine statistics response."""
    parcels_count: int
    projects_count: int
    analyses_count: int
    config: Dict[str, Any]


class ParcelCreate(BaseModel):
    """Create parcel request."""
    apn: str = ""
    state: str
    county: str
    municipality: str = ""
    address: str = ""
    acreage: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zoning_type: str = "agricultural"
    solar_permission: str = "unknown"
    owner_name: str = ""
    road_access: bool = True
    nearest_substation_mi: float = 0.0


class ParcelResponse(BaseModel):
    """Parcel response."""
    id: str
    apn: str
    state: str
    county: str
    municipality: str
    address: str
    acreage: float
    zoning_type: str
    solar_permission: str
    owner_name: str
    created_at: str


class ProjectCreate(BaseModel):
    """Create project request."""
    name: str
    project_type: str = "utility_solar"
    state: str = ""
    county: str = ""
    capacity_mw: float = 0.0


class ProjectResponse(BaseModel):
    """Project response."""
    id: str
    name: str
    project_type: str
    stage: str
    parcel_ids: List[str]
    total_acreage: float
    capacity_mw: float
    created_at: str


class AnalyzeRequest(BaseModel):
    """Site analysis request."""
    parcel_id: str
    project_type: str = "utility_solar"
    target_capacity_mw: float = 0.0
    include_financial: bool = True


class QuickScoreRequest(BaseModel):
    """Quick score request."""
    parcel_id: str


class SearchRequest(BaseModel):
    """Parcel search request."""
    query: str = ""
    states: List[str] = Field(default_factory=list)
    counties: List[str] = Field(default_factory=list)
    min_acreage: float = 0.0
    max_acreage: float = 999999.0
    zoning_types: List[str] = Field(default_factory=list)
    max_distance_to_substation_mi: float = 999.0
    limit: int = 100
    offset: int = 0


class AnalysisResponse(BaseModel):
    """Analysis response."""
    id: str
    parcel_id: str
    status: str
    overall_score: float
    permitting_score: float
    grid_score: float
    environmental_score: float
    land_score: float
    viability: str
    fatal_flaws: List[str]
    recommendations: List[str]
    duration_seconds: float


class SearchResponse(BaseModel):
    """Search response."""
    total_matches: int
    returned_count: int
    parcels: List[ParcelResponse]
    interpreted_query: str = ""
    search_duration_ms: float


# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_app(config: Optional[TerraJinkiConfig] = None) -> FastAPI:
    """Create FastAPI application."""

    config = config or get_config()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan handler."""
        # Startup
        logger.info(f"Starting TerraJinki API v{config.version}")
        app.state.engine = TerraJinkiEngine(config)
        app.state.active_connections: List[WebSocket] = []
        yield
        # Shutdown
        logger.info("Shutting down TerraJinki API")

    app = FastAPI(
        title="TerraJinki API",
        description="AI-powered renewable energy site intelligence platform",
        version=config.version,
        lifespan=lifespan,
        docs_url="/docs" if config.api.docs_enabled else None,
        redoc_url="/redoc" if config.api.docs_enabled else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # =========================================================================
    # DEPENDENCIES
    # =========================================================================

    def get_engine() -> TerraJinkiEngine:
        """Get engine instance."""
        return app.state.engine

    # =========================================================================
    # HEALTH & INFO ENDPOINTS
    # =========================================================================

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            version=config.version,
            timestamp=datetime.utcnow().isoformat(),
        )

    @app.get("/stats", response_model=StatsResponse, tags=["Health"])
    async def get_stats(engine: TerraJinkiEngine = Depends(get_engine)):
        """Get engine statistics."""
        return engine.get_stats()

    # =========================================================================
    # PARCEL ENDPOINTS
    # =========================================================================

    @app.post("/parcels", response_model=ParcelResponse, tags=["Parcels"])
    async def create_parcel(
        data: ParcelCreate,
        engine: TerraJinkiEngine = Depends(get_engine),
    ):
        """Create a new parcel."""
        try:
            zoning = ZoningType(data.zoning_type)
        except ValueError:
            zoning = ZoningType.AGRICULTURAL

        try:
            permission = SolarPermission(data.solar_permission)
        except ValueError:
            permission = SolarPermission.UNKNOWN

        centroid = None
        if data.latitude and data.longitude:
            centroid = GeoPoint(latitude=data.latitude, longitude=data.longitude)

        parcel = Parcel(
            apn=data.apn,
            state=data.state,
            county=data.county,
            municipality=data.municipality,
            address=data.address,
            acreage=data.acreage,
            centroid=centroid,
            zoning_type=zoning,
            solar_permission=permission,
            owner_name=data.owner_name,
            road_access=data.road_access,
            nearest_substation_mi=data.nearest_substation_mi,
        )

        result = await engine.create_parcel(parcel)

        return ParcelResponse(
            id=result.id,
            apn=result.apn,
            state=result.state,
            county=result.county,
            municipality=result.municipality,
            address=result.address,
            acreage=result.acreage,
            zoning_type=result.zoning_type.value,
            solar_permission=result.solar_permission.value,
            owner_name=result.owner_name,
            created_at=result.created_at.isoformat(),
        )

    @app.get("/parcels/{parcel_id}", response_model=ParcelResponse, tags=["Parcels"])
    async def get_parcel(
        parcel_id: str,
        engine: TerraJinkiEngine = Depends(get_engine),
    ):
        """Get parcel by ID."""
        parcel = await engine.get_parcel(parcel_id)
        if not parcel:
            raise HTTPException(status_code=404, detail="Parcel not found")

        return ParcelResponse(
            id=parcel.id,
            apn=parcel.apn,
            state=parcel.state,
            county=parcel.county,
            municipality=parcel.municipality,
            address=parcel.address,
            acreage=parcel.acreage,
            zoning_type=parcel.zoning_type.value,
            solar_permission=parcel.solar_permission.value,
            owner_name=parcel.owner_name,
            created_at=parcel.created_at.isoformat(),
        )

    @app.post("/parcels/search", response_model=SearchResponse, tags=["Parcels"])
    async def search_parcels(
        data: SearchRequest,
        engine: TerraJinkiEngine = Depends(get_engine),
    ):
        """Search parcels with filters."""
        from terrajinki.core.types import ParcelSearchQuery

        query = ParcelSearchQuery(
            query=data.query,
            states=data.states,
            counties=data.counties,
            min_acreage=data.min_acreage,
            max_acreage=data.max_acreage,
            limit=data.limit,
            offset=data.offset,
        )

        result = await engine.search_parcels(query)

        return SearchResponse(
            total_matches=result.total_matches,
            returned_count=result.returned_count,
            parcels=[
                ParcelResponse(
                    id=p.id,
                    apn=p.apn,
                    state=p.state,
                    county=p.county,
                    municipality=p.municipality,
                    address=p.address,
                    acreage=p.acreage,
                    zoning_type=p.zoning_type.value,
                    solar_permission=p.solar_permission.value,
                    owner_name=p.owner_name,
                    created_at=p.created_at.isoformat(),
                )
                for p in result.parcels
            ],
            interpreted_query=result.interpreted_query,
            search_duration_ms=result.search_duration_ms,
        )

    @app.post("/parcels/search/natural", response_model=SearchResponse, tags=["Parcels"])
    async def natural_language_search(
        query: str = Query(..., description="Natural language search query"),
        engine: TerraJinkiEngine = Depends(get_engine),
    ):
        """Search parcels using natural language."""
        result = await engine.natural_language_search(query)

        return SearchResponse(
            total_matches=result.total_matches,
            returned_count=result.returned_count,
            parcels=[
                ParcelResponse(
                    id=p.id,
                    apn=p.apn,
                    state=p.state,
                    county=p.county,
                    municipality=p.municipality,
                    address=p.address,
                    acreage=p.acreage,
                    zoning_type=p.zoning_type.value,
                    solar_permission=p.solar_permission.value,
                    owner_name=p.owner_name,
                    created_at=p.created_at.isoformat(),
                )
                for p in result.parcels
            ],
            interpreted_query=result.interpreted_query,
            search_duration_ms=result.search_duration_ms,
        )

    # =========================================================================
    # ANALYSIS ENDPOINTS
    # =========================================================================

    @app.post("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
    async def analyze_site(
        data: AnalyzeRequest,
        engine: TerraJinkiEngine = Depends(get_engine),
    ):
        """Perform comprehensive site analysis."""
        parcel = await engine.get_parcel(data.parcel_id)
        if not parcel:
            raise HTTPException(status_code=404, detail="Parcel not found")

        try:
            project_type = ProjectType(data.project_type)
        except ValueError:
            project_type = ProjectType.UTILITY_SOLAR

        analysis = await engine.analyze_site(
            parcel=parcel,
            project_type=project_type,
            target_capacity_mw=data.target_capacity_mw,
            include_financial=data.include_financial,
        )

        score = analysis.score or SiteScore()

        return AnalysisResponse(
            id=analysis.id,
            parcel_id=analysis.parcel_id,
            status="completed",
            overall_score=score.overall_score,
            permitting_score=score.permitting_score,
            grid_score=score.grid_score,
            environmental_score=score.environmental_score,
            land_score=score.land_score,
            viability=score.viability,
            fatal_flaws=score.fatal_flaws,
            recommendations=analysis.recommended_next_steps,
            duration_seconds=analysis.duration_seconds,
        )

    @app.post("/analyze/quick", tags=["Analysis"])
    async def quick_score(
        data: QuickScoreRequest,
        engine: TerraJinkiEngine = Depends(get_engine),
    ):
        """Get quick preliminary score."""
        parcel = await engine.get_parcel(data.parcel_id)
        if not parcel:
            raise HTTPException(status_code=404, detail="Parcel not found")

        return await engine.quick_score_parcel(parcel)

    # =========================================================================
    # PROJECT ENDPOINTS
    # =========================================================================

    @app.post("/projects", response_model=ProjectResponse, tags=["Projects"])
    async def create_project(
        data: ProjectCreate,
        engine: TerraJinkiEngine = Depends(get_engine),
    ):
        """Create a new project."""
        try:
            project_type = ProjectType(data.project_type)
        except ValueError:
            project_type = ProjectType.UTILITY_SOLAR

        project = Project(
            name=data.name,
            project_type=project_type,
            state=data.state,
            county=data.county,
            capacity_mw=data.capacity_mw,
        )

        result = await engine.create_project(project)

        return ProjectResponse(
            id=result.id,
            name=result.name,
            project_type=result.project_type.value,
            stage=result.stage.value,
            parcel_ids=result.parcel_ids,
            total_acreage=result.total_acreage,
            capacity_mw=result.capacity_mw,
            created_at=result.created_at.isoformat(),
        )

    @app.get("/projects", response_model=List[ProjectResponse], tags=["Projects"])
    async def list_projects(
        stage: Optional[str] = None,
        engine: TerraJinkiEngine = Depends(get_engine),
    ):
        """List all projects."""
        projects = await engine.list_projects(stage=stage)

        return [
            ProjectResponse(
                id=p.id,
                name=p.name,
                project_type=p.project_type.value,
                stage=p.stage.value,
                parcel_ids=p.parcel_ids,
                total_acreage=p.total_acreage,
                capacity_mw=p.capacity_mw,
                created_at=p.created_at.isoformat(),
            )
            for p in projects
        ]

    @app.get("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
    async def get_project(
        project_id: str,
        engine: TerraJinkiEngine = Depends(get_engine),
    ):
        """Get project by ID."""
        project = await engine.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return ProjectResponse(
            id=project.id,
            name=project.name,
            project_type=project.project_type.value,
            stage=project.stage.value,
            parcel_ids=project.parcel_ids,
            total_acreage=project.total_acreage,
            capacity_mw=project.capacity_mw,
            created_at=project.created_at.isoformat(),
        )

    @app.post("/projects/{project_id}/parcels/{parcel_id}", tags=["Projects"])
    async def add_parcel_to_project(
        project_id: str,
        parcel_id: str,
        engine: TerraJinkiEngine = Depends(get_engine),
    ):
        """Add parcel to project."""
        try:
            project = await engine.add_parcel_to_project(project_id, parcel_id)
            return {"status": "success", "project_id": project.id}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    # =========================================================================
    # WEBSOCKET ENDPOINTS
    # =========================================================================

    @app.websocket("/ws/analyze/{parcel_id}")
    async def websocket_analyze(
        websocket: WebSocket,
        parcel_id: str,
    ):
        """
        WebSocket endpoint for real-time analysis streaming.

        Streams progress updates as analysis proceeds.
        """
        await websocket.accept()
        engine = app.state.engine
        app.state.active_connections.append(websocket)

        try:
            parcel = await engine.get_parcel(parcel_id)
            if not parcel:
                await websocket.send_json({"error": "Parcel not found"})
                await websocket.close()
                return

            # Stream analysis progress
            async for progress in engine.analyze_site_streaming(parcel):
                await websocket.send_json({
                    "type": "progress",
                    "analysis_id": progress.analysis_id,
                    "status": progress.status,
                    "progress": progress.progress,
                    "current_step": progress.current_step,
                    "elapsed_seconds": progress.elapsed_seconds,
                    "estimated_remaining": progress.estimated_remaining_seconds,
                    "partial_results": progress.partial_results,
                })

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for parcel {parcel_id}")
        except Exception as e:
            logger.exception(f"WebSocket error: {e}")
            await websocket.send_json({"error": str(e)})
        finally:
            if websocket in app.state.active_connections:
                app.state.active_connections.remove(websocket)

    @app.websocket("/ws/copilot")
    async def websocket_copilot(websocket: WebSocket):
        """
        WebSocket endpoint for AI copilot chat.

        Enables conversational interaction with platform.
        """
        await websocket.accept()
        engine = app.state.engine
        app.state.active_connections.append(websocket)

        try:
            while True:
                # Receive message
                data = await websocket.receive_json()
                message = data.get("message", "")

                if not message:
                    continue

                # Process with AI copilot
                # In production, this would use a dedicated copilot agent
                response = {
                    "type": "response",
                    "message": f"I received: {message}",
                    "suggestions": [
                        "Search for parcels in Texas",
                        "Analyze a specific site",
                        "Show my project pipeline",
                    ],
                }

                await websocket.send_json(response)

        except WebSocketDisconnect:
            logger.info("Copilot WebSocket disconnected")
        except Exception as e:
            logger.exception(f"Copilot WebSocket error: {e}")
        finally:
            if websocket in app.state.active_connections:
                app.state.active_connections.remove(websocket)

    return app


# Create default app instance
app = create_app()


# Import SiteScore for type hints
from terrajinki.core.types import SiteScore
