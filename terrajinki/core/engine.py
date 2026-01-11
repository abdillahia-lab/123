"""
TerraJinki Engine

Main orchestration engine that coordinates all platform capabilities
including site analysis, search, and project management.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any, AsyncIterator
from uuid import uuid4
import asyncio
import logging

from terrajinki.core.types import (
    Parcel,
    Project,
    SiteAnalysis,
    SiteScore,
    SearchResult,
    ParcelSearchQuery,
    ProjectType,
    GeoPoint,
    BoundingBox,
)
from terrajinki.core.config import TerraJinkiConfig, get_config
from terrajinki.agents.base import AgentContext
from terrajinki.agents.orchestrator import OrchestratorAgent, AnalysisRequest, WorkflowEngine

logger = logging.getLogger(__name__)


@dataclass
class AnalysisProgress:
    """Real-time progress update for analysis."""
    analysis_id: str
    status: str  # started, running, completed, failed
    progress: float  # 0.0 - 1.0
    current_step: str
    elapsed_seconds: float
    estimated_remaining_seconds: float
    partial_results: Dict[str, Any] = field(default_factory=dict)


class TerraJinkiEngine:
    """
    Main engine for TerraJinki platform.

    Provides unified interface for:
    - Site analysis with real-time progress
    - Parcel search with natural language
    - Project management
    - Human-in-the-loop workflows
    """

    def __init__(self, config: Optional[TerraJinkiConfig] = None):
        self.config = config or get_config()
        self._context: Optional[AgentContext] = None
        self._orchestrator: Optional[OrchestratorAgent] = None
        self._workflow_engine: Optional[WorkflowEngine] = None

        # In-memory storage (would be database in production)
        self._parcels: Dict[str, Parcel] = {}
        self._projects: Dict[str, Project] = {}
        self._analyses: Dict[str, SiteAnalysis] = {}

        # Progress callbacks for real-time updates
        self._progress_callbacks: Dict[str, List[Any]] = {}

    def _get_context(self) -> AgentContext:
        """Get or create agent context."""
        if self._context is None:
            self._context = AgentContext(config=self.config)
            self._context.on_progress = self._handle_progress
        return self._context

    def _get_orchestrator(self) -> OrchestratorAgent:
        """Get or create orchestrator."""
        if self._orchestrator is None:
            self._orchestrator = OrchestratorAgent(self._get_context())
        return self._orchestrator

    def _get_workflow_engine(self) -> WorkflowEngine:
        """Get or create workflow engine."""
        if self._workflow_engine is None:
            self._workflow_engine = WorkflowEngine(self._get_context())
        return self._workflow_engine

    async def _handle_progress(self, agent: str, progress: float, status: str):
        """Handle progress updates from agents."""
        # Would broadcast to WebSocket clients
        logger.debug(f"Progress: {agent} - {progress:.0%} - {status}")

    # =========================================================================
    # SITE ANALYSIS
    # =========================================================================

    async def analyze_site(
        self,
        parcel: Parcel,
        project_type: ProjectType = ProjectType.UTILITY_SOLAR,
        target_capacity_mw: float = 0.0,
        include_financial: bool = True,
        user_id: str = "",
    ) -> SiteAnalysis:
        """
        Perform comprehensive site analysis.

        Args:
            parcel: Parcel to analyze
            project_type: Type of project
            target_capacity_mw: Target capacity (0 = auto-calculate)
            include_financial: Include financial analysis
            user_id: User requesting analysis

        Returns:
            Complete SiteAnalysis result
        """
        request = AnalysisRequest(
            parcel=parcel,
            project_type=project_type,
            target_capacity_mw=target_capacity_mw,
            include_financial=include_financial,
            requester_id=user_id,
        )

        orchestrator = self._get_orchestrator()

        # Call execute directly to get SiteAnalysis (not run() which wraps in AgentResult)
        try:
            analysis = await orchestrator.execute(request)
            self._analyses[analysis.id] = analysis
            return analysis
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")

    async def analyze_site_streaming(
        self,
        parcel: Parcel,
        project_type: ProjectType = ProjectType.UTILITY_SOLAR,
    ) -> AsyncIterator[AnalysisProgress]:
        """
        Perform site analysis with streaming progress updates.

        Yields AnalysisProgress updates as analysis proceeds.
        """
        analysis_id = str(uuid4())
        start_time = datetime.utcnow()

        yield AnalysisProgress(
            analysis_id=analysis_id,
            status="started",
            progress=0.0,
            current_step="Initializing analysis",
            elapsed_seconds=0,
            estimated_remaining_seconds=60,
        )

        try:
            request = AnalysisRequest(
                parcel=parcel,
                project_type=project_type,
            )

            # Create progress tracking
            progress_queue: asyncio.Queue = asyncio.Queue()

            async def progress_callback(agent: str, progress: float, status: str):
                await progress_queue.put((agent, progress, status))

            context = self._get_context()
            context.on_progress = progress_callback

            # Start analysis in background
            orchestrator = OrchestratorAgent(context)
            analysis_task = asyncio.create_task(orchestrator.run(request))

            # Stream progress updates
            while not analysis_task.done():
                try:
                    agent, progress, status = await asyncio.wait_for(
                        progress_queue.get(),
                        timeout=0.5
                    )

                    elapsed = (datetime.utcnow() - start_time).total_seconds()

                    yield AnalysisProgress(
                        analysis_id=analysis_id,
                        status="running",
                        progress=progress,
                        current_step=f"{agent}: {status}",
                        elapsed_seconds=elapsed,
                        estimated_remaining_seconds=max(0, 60 - elapsed),
                    )

                except asyncio.TimeoutError:
                    continue

            # Get final result
            result = await analysis_task
            elapsed = (datetime.utcnow() - start_time).total_seconds()

            if result.success:
                yield AnalysisProgress(
                    analysis_id=analysis_id,
                    status="completed",
                    progress=1.0,
                    current_step="Analysis complete",
                    elapsed_seconds=elapsed,
                    estimated_remaining_seconds=0,
                    partial_results={"analysis": result.output},
                )
            else:
                yield AnalysisProgress(
                    analysis_id=analysis_id,
                    status="failed",
                    progress=result.score / 100 if result.score else 0,
                    current_step=f"Failed: {result.error_message}",
                    elapsed_seconds=elapsed,
                    estimated_remaining_seconds=0,
                )

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            yield AnalysisProgress(
                analysis_id=analysis_id,
                status="failed",
                progress=0,
                current_step=f"Error: {str(e)}",
                elapsed_seconds=elapsed,
                estimated_remaining_seconds=0,
            )

    async def quick_score_parcel(self, parcel: Parcel) -> Dict[str, Any]:
        """
        Get quick preliminary score without full analysis.

        Useful for rapid screening of many parcels.
        """
        orchestrator = self._get_orchestrator()
        return await orchestrator.quick_score(parcel)

    async def batch_score_parcels(
        self,
        parcels: List[Parcel],
        max_concurrent: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Score multiple parcels in parallel.

        Args:
            parcels: List of parcels to score
            max_concurrent: Maximum concurrent analyses

        Returns:
            List of quick scores in same order as input
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def score_with_limit(parcel: Parcel) -> Dict[str, Any]:
            async with semaphore:
                return await self.quick_score_parcel(parcel)

        tasks = [score_with_limit(p) for p in parcels]
        return await asyncio.gather(*tasks)

    # =========================================================================
    # PARCEL SEARCH
    # =========================================================================

    async def search_parcels(
        self,
        query: ParcelSearchQuery,
    ) -> SearchResult:
        """
        Search parcels with natural language or structured filters.

        Args:
            query: Search query with filters

        Returns:
            SearchResult with matching parcels
        """
        start_time = datetime.utcnow()

        # In production, this would query PostGIS
        # For now, filter in-memory parcels
        matching = []

        for parcel in self._parcels.values():
            if self._matches_query(parcel, query):
                matching.append(parcel)

        # Sort
        if query.sort_by == "score":
            matching.sort(key=lambda p: getattr(p, "latest_score", 0), reverse=True)
        elif query.sort_by == "acreage":
            matching.sort(key=lambda p: p.acreage, reverse=query.sort_order == "desc")

        # Paginate
        total = len(matching)
        matching = matching[query.offset:query.offset + query.limit]

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        return SearchResult(
            query=query,
            total_matches=total,
            returned_count=len(matching),
            parcels=matching,
            search_duration_ms=duration,
        )

    def _matches_query(self, parcel: Parcel, query: ParcelSearchQuery) -> bool:
        """Check if parcel matches search query."""
        # State filter
        if query.states and parcel.state not in query.states:
            return False

        # County filter
        if query.counties and parcel.county not in query.counties:
            return False

        # Acreage filter
        if parcel.acreage < query.min_acreage or parcel.acreage > query.max_acreage:
            return False

        # Zoning filter
        if query.zoning_types and parcel.zoning_type not in query.zoning_types:
            return False

        # Bounding box filter
        if query.bounding_box and parcel.centroid:
            if not query.bounding_box.contains(parcel.centroid):
                return False

        # Near point filter
        if query.near_point and parcel.centroid:
            distance = parcel.centroid.distance_to(query.near_point)
            if distance > query.near_point_radius_mi:
                return False

        return True

    async def natural_language_search(self, query: str) -> SearchResult:
        """
        Search parcels using natural language query.

        Args:
            query: Natural language query like "50+ acres in Texas near substations"

        Returns:
            SearchResult with matching parcels
        """
        # Use LLM to parse natural language into structured query
        orchestrator = self._get_orchestrator()

        prompt = f"""Parse this natural language parcel search query into structured filters.

QUERY: "{query}"

Extract:
- states: List of state abbreviations
- min_acreage: Minimum acreage
- max_acreage: Maximum acreage (use 999999 if not specified)
- zoning_types: List of zoning types (agricultural, residential, commercial, industrial)
- max_distance_to_substation: Maximum miles to substation
- other_requirements: Any other filters mentioned

Respond in JSON:
{{
    "states": [],
    "counties": [],
    "min_acreage": 0,
    "max_acreage": 999999,
    "zoning_types": [],
    "max_distance_to_substation_mi": 999,
    "interpreted_query": "human-readable interpretation"
}}"""

        result = await orchestrator.call_llm(prompt, json_mode=True)

        # Build structured query
        from terrajinki.core.types import ZoningType

        zoning_types = []
        for zt in result.get("zoning_types", []):
            try:
                zoning_types.append(ZoningType(zt))
            except ValueError:
                pass

        structured_query = ParcelSearchQuery(
            query=query,
            states=result.get("states", []),
            counties=result.get("counties", []),
            min_acreage=result.get("min_acreage", 0),
            max_acreage=result.get("max_acreage", float("inf")),
            zoning_types=zoning_types,
            max_distance_to_substation_mi=result.get("max_distance_to_substation_mi", float("inf")),
        )

        search_result = await self.search_parcels(structured_query)
        search_result.interpreted_query = result.get("interpreted_query", query)

        return search_result

    # =========================================================================
    # PARCEL MANAGEMENT
    # =========================================================================

    async def create_parcel(self, parcel: Parcel) -> Parcel:
        """Create a new parcel."""
        if not parcel.id:
            parcel.id = str(uuid4())
        parcel.created_at = datetime.utcnow()
        parcel.updated_at = datetime.utcnow()
        self._parcels[parcel.id] = parcel
        return parcel

    async def get_parcel(self, parcel_id: str) -> Optional[Parcel]:
        """Get parcel by ID."""
        return self._parcels.get(parcel_id)

    async def update_parcel(self, parcel: Parcel) -> Parcel:
        """Update existing parcel."""
        parcel.updated_at = datetime.utcnow()
        self._parcels[parcel.id] = parcel
        return parcel

    async def delete_parcel(self, parcel_id: str) -> bool:
        """Delete parcel."""
        if parcel_id in self._parcels:
            del self._parcels[parcel_id]
            return True
        return False

    # =========================================================================
    # PROJECT MANAGEMENT
    # =========================================================================

    async def create_project(self, project: Project) -> Project:
        """Create a new project."""
        if not project.id:
            project.id = str(uuid4())
        project.created_at = datetime.utcnow()
        project.updated_at = datetime.utcnow()
        self._projects[project.id] = project
        return project

    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        return self._projects.get(project_id)

    async def list_projects(
        self,
        user_id: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> List[Project]:
        """List projects with optional filters."""
        projects = list(self._projects.values())

        if user_id:
            projects = [p for p in projects if p.owner_id == user_id]

        if stage:
            from terrajinki.core.types import ProjectStage
            try:
                stage_enum = ProjectStage(stage)
                projects = [p for p in projects if p.stage == stage_enum]
            except ValueError:
                pass

        return projects

    async def update_project(self, project: Project) -> Project:
        """Update existing project."""
        project.updated_at = datetime.utcnow()
        self._projects[project.id] = project
        return project

    async def add_parcel_to_project(
        self,
        project_id: str,
        parcel_id: str,
    ) -> Project:
        """Add parcel to project."""
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        if parcel_id not in project.parcel_ids:
            project.parcel_ids.append(parcel_id)

            # Update total acreage
            parcel = await self.get_parcel(parcel_id)
            if parcel:
                project.total_acreage += parcel.acreage

            project.updated_at = datetime.utcnow()
            self._projects[project.id] = project

        return project

    # =========================================================================
    # WORKFLOW MANAGEMENT
    # =========================================================================

    async def start_analysis_workflow(
        self,
        parcel: Parcel,
        project_type: ProjectType = ProjectType.UTILITY_SOLAR,
        user_id: str = "",
    ) -> str:
        """
        Start analysis as a persistent workflow.

        Returns workflow ID for tracking and resumption.
        """
        request = AnalysisRequest(
            parcel=parcel,
            project_type=project_type,
            requester_id=user_id,
        )

        workflow_engine = self._get_workflow_engine()
        return await workflow_engine.start_workflow("site_analysis", request)

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow status."""
        workflow_engine = self._get_workflow_engine()
        return await workflow_engine.get_workflow_status(workflow_id)

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "parcels_count": len(self._parcels),
            "projects_count": len(self._projects),
            "analyses_count": len(self._analyses),
            "config": {
                "environment": self.config.environment.value,
                "satellite_enabled": self.config.enable_satellite_analysis,
                "gnn_enabled": self.config.enable_gnn_grid_analysis,
                "rag_enabled": self.config.enable_rag_ordinances,
                "hitl_enabled": self.config.enable_human_in_loop,
            },
        }
