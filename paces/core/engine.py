"""
Paces Engine - Main orchestration for renewable energy site development platform.

Coordinates all modules:
- Parcel search and discovery
- AI-powered site analysis
- Permitting prediction
- Grid interconnection analysis
- Environmental screening
- Financial modeling
- Report generation
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional, Callable
from uuid import uuid4

from loguru import logger

from paces.core.config import PacesConfig, load_config
from paces.core.types import (
    Parcel,
    Project,
    Jurisdiction,
    SiteScore,
    FeasibilityReport,
    ProjectType,
    GeoPoint,
    BoundingBox,
)
from paces.agents.site import SiteAnalysisAgent, SiteAnalysisConfig
from paces.agents.permitting import PermittingAgent
from paces.agents.grid import GridAgent
from paces.agents.environmental import EnvironmentalAgent
from paces.agents.report import ReportAgent
from paces.financial.analyzer import FinancialAnalyzer, FinancialAssumptions


class PacesEngine:
    """
    Main orchestration engine for Paces platform.

    Provides:
    - Parcel search and filtering
    - Comprehensive site analysis
    - AI-powered permitting prediction
    - Grid interconnection assessment
    - Environmental screening
    - Financial modeling
    - Report generation
    - Project pipeline management
    """

    def __init__(self, config: Optional[PacesConfig] = None):
        self.config = config or load_config()
        self.config.ensure_directories()

        # Agents
        self._site_agent: Optional[SiteAnalysisAgent] = None
        self._permitting_agent: Optional[PermittingAgent] = None
        self._grid_agent: Optional[GridAgent] = None
        self._environmental_agent: Optional[EnvironmentalAgent] = None
        self._report_agent: Optional[ReportAgent] = None

        # Analyzers
        self._financial_analyzer: Optional[FinancialAnalyzer] = None

        # Data stores (in production, would be database)
        self._parcels: dict[str, Parcel] = {}
        self._projects: dict[str, Project] = {}
        self._jurisdictions: dict[str, Jurisdiction] = {}

        # State
        self._initialized = False

        logger.info("Paces Engine created")

    async def initialize(self) -> bool:
        """Initialize all engine components."""
        logger.info("Initializing Paces Engine...")

        try:
            # Initialize agents
            self._site_agent = SiteAnalysisAgent()
            self._permitting_agent = PermittingAgent()
            self._grid_agent = GridAgent()
            self._environmental_agent = EnvironmentalAgent()
            self._report_agent = ReportAgent()

            await asyncio.gather(
                self._site_agent.initialize(),
                self._permitting_agent.initialize(),
                self._grid_agent.initialize(),
                self._environmental_agent.initialize(),
                self._report_agent.initialize(),
            )

            # Initialize analyzers
            self._financial_analyzer = FinancialAnalyzer()

            self._initialized = True
            logger.info("Paces Engine initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Engine initialization failed: {e}")
            return False

    # =========================================================================
    # Parcel Operations
    # =========================================================================

    async def search_parcels(
        self,
        state: str = None,
        county: str = None,
        min_acreage: float = None,
        max_acreage: float = None,
        zoning_types: list[str] = None,
        bounding_box: BoundingBox = None,
        limit: int = 100,
    ) -> list[Parcel]:
        """
        Search for parcels matching criteria.

        Args:
            state: Filter by state
            county: Filter by county
            min_acreage: Minimum acreage
            max_acreage: Maximum acreage
            zoning_types: Allowed zoning types
            bounding_box: Geographic bounding box
            limit: Maximum results

        Returns:
            List of matching parcels
        """
        logger.info(f"Searching parcels: state={state}, county={county}")

        # In production, would query parcel database/API
        # For now, return from in-memory store
        results = []

        for parcel in self._parcels.values():
            if state and parcel.state.upper() != state.upper():
                continue
            if county and parcel.county.upper() != county.upper():
                continue
            if min_acreage and parcel.acreage < min_acreage:
                continue
            if max_acreage and parcel.acreage > max_acreage:
                continue
            if zoning_types and parcel.zoning_type.value not in zoning_types:
                continue
            if bounding_box and parcel.centroid:
                if not bounding_box.contains(parcel.centroid):
                    continue

            results.append(parcel)

            if len(results) >= limit:
                break

        logger.info(f"Found {len(results)} parcels")
        return results

    def add_parcel(self, parcel: Parcel) -> Parcel:
        """Add a parcel to the database."""
        self._parcels[parcel.id] = parcel
        return parcel

    def get_parcel(self, parcel_id: str) -> Optional[Parcel]:
        """Get a parcel by ID."""
        return self._parcels.get(parcel_id)

    # =========================================================================
    # Site Analysis
    # =========================================================================

    async def analyze_site(
        self,
        parcel: Parcel,
        project_type: ProjectType = ProjectType.UTILITY_SOLAR,
        target_capacity_mw: float = 5.0,
        jurisdiction: Jurisdiction = None,
    ) -> FeasibilityReport:
        """
        Perform comprehensive site analysis.

        Args:
            parcel: Parcel to analyze
            project_type: Type of project
            target_capacity_mw: Target capacity
            jurisdiction: Optional jurisdiction data

        Returns:
            Complete FeasibilityReport
        """
        if not self._initialized:
            raise RuntimeError("Engine not initialized")

        logger.info(f"Analyzing site: {parcel.id}")

        config = SiteAnalysisConfig(
            project_type=project_type,
            target_capacity_mw=target_capacity_mw,
        )

        result = await self._site_agent.execute(
            parcel=parcel,
            jurisdiction=jurisdiction,
            config=config,
        )

        if not result.success:
            logger.error(f"Site analysis failed: {result.error}")
            return None

        # Extract feasibility report from result
        return FeasibilityReport(
            parcel_id=parcel.id,
            parcel=parcel,
            site_score=SiteScore(**result.data.get("site_score", {})) if result.data.get("site_score") else None,
            overall_viability=result.data.get("feasibility", {}).get("overall_viability", "unknown"),
            executive_summary=result.analysis,
            proceed_recommendation=result.data.get("site_score", {}).get("proceed_recommendation", "unknown"),
            key_risks=result.risks,
            next_steps=result.recommendations[:5],
        )

    async def analyze_multiple_sites(
        self,
        parcels: list[Parcel],
        project_type: ProjectType = ProjectType.UTILITY_SOLAR,
        target_capacity_mw: float = 5.0,
    ) -> list[FeasibilityReport]:
        """
        Analyze multiple sites and rank them.

        Args:
            parcels: List of parcels to analyze
            project_type: Type of project
            target_capacity_mw: Target capacity

        Returns:
            List of FeasibilityReports sorted by score
        """
        logger.info(f"Analyzing {len(parcels)} sites")

        reports = []
        for parcel in parcels:
            try:
                report = await self.analyze_site(
                    parcel,
                    project_type=project_type,
                    target_capacity_mw=target_capacity_mw,
                )
                if report:
                    reports.append(report)
            except Exception as e:
                logger.warning(f"Failed to analyze parcel {parcel.id}: {e}")

        # Sort by score
        reports.sort(
            key=lambda r: r.site_score.overall_score if r.site_score else 0,
            reverse=True,
        )

        return reports

    # =========================================================================
    # Permitting
    # =========================================================================

    async def analyze_permitting(
        self,
        parcel: Parcel,
        jurisdiction: Jurisdiction = None,
        ordinance_text: str = None,
        capacity_mw: float = 5.0,
    ) -> dict:
        """
        Analyze permitting requirements for a parcel.

        Uses LLM to parse zoning ordinances and predict permitting risk.
        """
        if not self._initialized:
            raise RuntimeError("Engine not initialized")

        result = await self._permitting_agent.execute(
            parcel=parcel,
            jurisdiction=jurisdiction,
            ordinance_text=ordinance_text or "",
            capacity_mw=capacity_mw,
        )

        return result.data if result.success else {"error": result.error}

    def add_jurisdiction(self, jurisdiction: Jurisdiction) -> Jurisdiction:
        """Add a jurisdiction to the database."""
        self._jurisdictions[jurisdiction.id] = jurisdiction
        return jurisdiction

    def get_jurisdiction(self, jurisdiction_id: str) -> Optional[Jurisdiction]:
        """Get a jurisdiction by ID."""
        return self._jurisdictions.get(jurisdiction_id)

    # =========================================================================
    # Grid Analysis
    # =========================================================================

    async def analyze_grid(
        self,
        parcel: Parcel,
        capacity_mw: float = 5.0,
    ) -> dict:
        """
        Analyze grid interconnection for a parcel.

        Returns substation proximity, capacity, queue analysis, and cost estimates.
        """
        if not self._initialized:
            raise RuntimeError("Engine not initialized")

        result = await self._grid_agent.execute(
            parcel=parcel,
            project_capacity_mw=capacity_mw,
        )

        return result.data if result.success else {"error": result.error}

    # =========================================================================
    # Environmental
    # =========================================================================

    async def screen_environmental(
        self,
        parcel: Parcel,
        detailed: bool = False,
    ) -> dict:
        """
        Screen parcel for environmental constraints.

        Checks wetlands, flood zones, endangered species, cultural resources.
        """
        if not self._initialized:
            raise RuntimeError("Engine not initialized")

        result = await self._environmental_agent.execute(
            parcel=parcel,
            detailed_analysis=detailed,
        )

        return result.data if result.success else {"error": result.error}

    # =========================================================================
    # Financial
    # =========================================================================

    def analyze_financials(
        self,
        parcel: Parcel,
        assumptions: FinancialAssumptions = None,
    ) -> dict:
        """
        Perform financial analysis for a solar project on the parcel.

        Returns CAPEX, OPEX, NPV, IRR, LCOE, and payback period.
        """
        if not self._financial_analyzer:
            raise RuntimeError("Financial analyzer not initialized")

        financials = self._financial_analyzer.analyze(
            parcel=parcel,
            assumptions=assumptions,
        )

        return financials.to_dict()

    def calculate_min_ppa(
        self,
        parcel: Parcel,
        target_irr: float = 0.10,
    ) -> float:
        """Calculate minimum PPA price to achieve target IRR."""
        return self._financial_analyzer.calculate_min_ppa_price(
            parcel=parcel,
            target_irr=target_irr,
        )

    # =========================================================================
    # Reports
    # =========================================================================

    async def generate_report(
        self,
        feasibility: FeasibilityReport,
        format: str = "markdown",
    ) -> str:
        """
        Generate feasibility report.

        Args:
            feasibility: FeasibilityReport data
            format: Output format (markdown, html)

        Returns:
            Generated report content
        """
        result = await self._report_agent.execute(
            feasibility=feasibility,
            output_format=format,
        )

        return result.data.get("report", "") if result.success else ""

    # =========================================================================
    # Projects
    # =========================================================================

    def create_project(
        self,
        name: str,
        parcel_ids: list[str],
        project_type: ProjectType = ProjectType.UTILITY_SOLAR,
        capacity_mw: float = 5.0,
    ) -> Project:
        """Create a new project."""
        project = Project(
            name=name,
            parcel_ids=parcel_ids,
            project_type=project_type,
            capacity_mw_dc=capacity_mw,
        )
        self._projects[project.id] = project
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        return self._projects.get(project_id)

    def list_projects(self) -> list[Project]:
        """List all projects."""
        return list(self._projects.values())

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_stats(self) -> dict:
        """Get engine statistics."""
        return {
            "initialized": self._initialized,
            "parcels_count": len(self._parcels),
            "projects_count": len(self._projects),
            "jurisdictions_count": len(self._jurisdictions),
        }

    async def health_check(self) -> dict:
        """Perform health check."""
        return {
            "status": "healthy" if self._initialized else "not_initialized",
            "timestamp": datetime.now().isoformat(),
        }

    async def shutdown(self) -> None:
        """Shutdown engine."""
        logger.info("Shutting down Paces Engine")
        self._initialized = False
