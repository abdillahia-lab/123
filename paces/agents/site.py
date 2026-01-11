"""
Site Analysis Agent - Comprehensive site evaluation orchestrator.

Coordinates all analysis agents to produce complete site assessment:
- Permitting analysis
- Grid interconnection
- Environmental screening
- Solar resource assessment
- Financial modeling
- Overall scoring
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from loguru import logger

from paces.agents.base import BaseAgent, AgentResult
from paces.agents.permitting import PermittingAgent
from paces.agents.grid import GridAgent
from paces.agents.environmental import EnvironmentalAgent
from paces.core.types import (
    Parcel,
    Jurisdiction,
    SiteScore,
    FeasibilityReport,
    ProjectType,
)


@dataclass
class SiteAnalysisConfig:
    """Configuration for site analysis."""
    project_type: ProjectType = ProjectType.UTILITY_SOLAR
    target_capacity_mw: float = 5.0
    include_permitting: bool = True
    include_grid: bool = True
    include_environmental: bool = True
    include_financial: bool = True
    detailed_ai_analysis: bool = True


class SiteAnalysisAgent(BaseAgent):
    """
    Master orchestration agent for comprehensive site analysis.

    Coordinates:
    - PermittingAgent: Zoning and permit analysis
    - GridAgent: Interconnection assessment
    - EnvironmentalAgent: Environmental screening
    - Financial modeling
    - Overall site scoring
    """

    def __init__(self):
        super().__init__(
            name="SiteAnalysisAgent",
            model="claude-3-5-sonnet-20241022",
        )

        # Sub-agents
        self._permitting_agent = PermittingAgent()
        self._grid_agent = GridAgent()
        self._environmental_agent = EnvironmentalAgent()

    async def initialize(self) -> bool:
        """Initialize all sub-agents."""
        try:
            await asyncio.gather(
                self._permitting_agent.initialize(),
                self._grid_agent.initialize(),
                self._environmental_agent.initialize(),
            )
            self._initialized = True
            logger.info("SiteAnalysisAgent initialized with all sub-agents")
            return True
        except Exception as e:
            logger.error(f"SiteAnalysisAgent initialization failed: {e}")
            return False

    async def execute(
        self,
        parcel: Parcel,
        jurisdiction: Jurisdiction = None,
        config: SiteAnalysisConfig = None,
    ) -> AgentResult:
        """
        Execute comprehensive site analysis.

        Args:
            parcel: Parcel to analyze
            jurisdiction: Optional jurisdiction data
            config: Analysis configuration

        Returns:
            AgentResult with complete site analysis
        """
        start_time = datetime.now()
        config = config or SiteAnalysisConfig()

        logger.info(f"Starting comprehensive site analysis for parcel {parcel.id}")

        try:
            # Run analyses in parallel where possible
            tasks = []

            if config.include_permitting:
                tasks.append(self._run_permitting(parcel, jurisdiction, config))

            if config.include_grid:
                tasks.append(self._run_grid(parcel, config))

            if config.include_environmental:
                tasks.append(self._run_environmental(parcel, config))

            # Execute all analyses
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Parse results
            permitting_result = None
            grid_result = None
            environmental_result = None

            idx = 0
            if config.include_permitting:
                permitting_result = results[idx] if not isinstance(results[idx], Exception) else None
                idx += 1
            if config.include_grid:
                grid_result = results[idx] if not isinstance(results[idx], Exception) else None
                idx += 1
            if config.include_environmental:
                environmental_result = results[idx] if not isinstance(results[idx], Exception) else None

            # Calculate overall site score
            site_score = self._calculate_site_score(
                parcel,
                permitting_result,
                grid_result,
                environmental_result,
                config,
            )

            # Generate feasibility report
            feasibility = self._generate_feasibility_report(
                parcel,
                site_score,
                permitting_result,
                grid_result,
                environmental_result,
                config,
            )

            # Compile all risks
            all_risks = []
            all_recommendations = []

            if permitting_result and permitting_result.success:
                all_risks.extend(permitting_result.risks)
                all_recommendations.extend(permitting_result.recommendations)

            if grid_result and grid_result.success:
                all_risks.extend(grid_result.risks)
                all_recommendations.extend(grid_result.recommendations)

            if environmental_result and environmental_result.success:
                all_risks.extend(environmental_result.risks)
                all_recommendations.extend(environmental_result.recommendations)

            # Generate executive summary
            summary = await self._generate_executive_summary(
                parcel,
                site_score,
                all_risks,
                config,
            )

            return self._build_result(
                success=True,
                data={
                    "site_score": site_score.to_dict(),
                    "feasibility": feasibility.to_dict(),
                    "permitting": permitting_result.data if permitting_result else None,
                    "grid": grid_result.data if grid_result else None,
                    "environmental": environmental_result.data if environmental_result else None,
                },
                analysis=summary,
                confidence=site_score.overall_score / 100,
                recommendations=all_recommendations[:10],  # Top 10
                risks=all_risks,
                start_time=start_time,
            )

        except Exception as e:
            logger.error(f"Site analysis failed: {e}")
            return self._build_result(
                success=False,
                error=str(e),
                start_time=start_time,
            )

    async def _run_permitting(
        self,
        parcel: Parcel,
        jurisdiction: Jurisdiction,
        config: SiteAnalysisConfig,
    ) -> AgentResult:
        """Run permitting analysis."""
        return await self._permitting_agent.execute(
            parcel=parcel,
            jurisdiction=jurisdiction,
            project_type=config.project_type.value,
            capacity_mw=config.target_capacity_mw,
        )

    async def _run_grid(
        self,
        parcel: Parcel,
        config: SiteAnalysisConfig,
    ) -> AgentResult:
        """Run grid analysis."""
        return await self._grid_agent.execute(
            parcel=parcel,
            project_capacity_mw=config.target_capacity_mw,
        )

    async def _run_environmental(
        self,
        parcel: Parcel,
        config: SiteAnalysisConfig,
    ) -> AgentResult:
        """Run environmental screening."""
        return await self._environmental_agent.execute(
            parcel=parcel,
            detailed_analysis=config.detailed_ai_analysis,
        )

    def _calculate_site_score(
        self,
        parcel: Parcel,
        permitting_result: Optional[AgentResult],
        grid_result: Optional[AgentResult],
        environmental_result: Optional[AgentResult],
        config: SiteAnalysisConfig,
    ) -> SiteScore:
        """Calculate comprehensive site score."""
        score = SiteScore(parcel_id=parcel.id)

        # Permitting score (weight: 30%)
        if permitting_result and permitting_result.success:
            score.permitting_score = permitting_result.data.get("permitting_score", 50)
            score.permitting_factors = {
                "permission_type": permitting_result.data.get("solar_permission", "unknown"),
                "public_hearing": permitting_result.data.get("public_hearing_required", False),
            }
        else:
            score.permitting_score = 50  # Default if no analysis

        # Grid score (weight: 30%)
        if grid_result and grid_result.success:
            score.grid_score = grid_result.data.get("grid_score", 50)
            score.grid_factors = {
                "distance_miles": grid_result.data.get("grid_connection", {}).get("distance_to_substation_miles", 0),
                "cost_per_mw": grid_result.data.get("cost_breakdown", {}).get("cost_per_mw", 0),
            }
        else:
            score.grid_score = 50

        # Environmental score (weight: 20%)
        if environmental_result and environmental_result.success:
            score.environmental_score = environmental_result.data.get("environmental_score", 80)
            score.environmental_factors = {
                "risk_level": environmental_result.data.get("overall_risk", "LOW"),
                "constraints": environmental_result.data.get("constraints", []),
            }
        else:
            score.environmental_score = 80

        # Land score (weight: 20%)
        score.land_score = self._calculate_land_score(parcel, config)
        score.land_factors = {
            "acreage": parcel.acreage,
            "usable_acreage": parcel.usable_acreage or parcel.acreage,
            "slope": parcel.avg_slope_pct,
        }

        # Calculate overall score (weighted average)
        score.overall_score = (
            score.permitting_score * 0.30 +
            score.grid_score * 0.30 +
            score.environmental_score * 0.20 +
            score.land_score * 0.20
        )

        # Identify fatal flaws
        score.fatal_flaws = []
        if permitting_result and permitting_result.risks:
            for risk in permitting_result.risks:
                if "FATAL" in risk.upper():
                    score.fatal_flaws.append(risk)

        if environmental_result and environmental_result.risks:
            for risk in environmental_result.risks:
                if "FATAL" in risk.upper():
                    score.fatal_flaws.append(risk)

        # Set recommendation
        if score.fatal_flaws:
            score.proceed_recommendation = "avoid"
        elif score.overall_score >= 70:
            score.proceed_recommendation = "proceed"
        elif score.overall_score >= 50:
            score.proceed_recommendation = "conditional"
        else:
            score.proceed_recommendation = "avoid"

        return score

    def _calculate_land_score(self, parcel: Parcel, config: SiteAnalysisConfig) -> float:
        """Calculate land suitability score."""
        score = 100.0

        # Acreage check
        required_acres = config.target_capacity_mw * 6  # ~6 acres per MW
        if parcel.acreage < required_acres:
            score -= 50  # Insufficient land

        # Slope penalty
        if parcel.avg_slope_pct > 15:
            score -= 30
        elif parcel.avg_slope_pct > 10:
            score -= 15
        elif parcel.avg_slope_pct > 5:
            score -= 5

        # Road access
        if not parcel.road_access:
            score -= 20

        return max(0, score)

    def _generate_feasibility_report(
        self,
        parcel: Parcel,
        site_score: SiteScore,
        permitting_result: Optional[AgentResult],
        grid_result: Optional[AgentResult],
        environmental_result: Optional[AgentResult],
        config: SiteAnalysisConfig,
    ) -> FeasibilityReport:
        """Generate feasibility report."""
        report = FeasibilityReport(
            parcel_id=parcel.id,
            parcel=parcel,
            site_score=site_score,
        )

        # Set viability
        if site_score.overall_score >= 80:
            report.overall_viability = "excellent"
        elif site_score.overall_score >= 65:
            report.overall_viability = "good"
        elif site_score.overall_score >= 50:
            report.overall_viability = "fair"
        elif site_score.overall_score >= 30:
            report.overall_viability = "poor"
        else:
            report.overall_viability = "not_viable"

        report.proceed_recommendation = site_score.proceed_recommendation
        report.recommended_capacity_mw = min(
            config.target_capacity_mw,
            parcel.acreage / 6  # Max based on land
        )

        # Estimate costs
        if grid_result and grid_result.success:
            interconnection_cost = grid_result.data.get("cost_breakdown", {}).get("total_cost", 0)
        else:
            interconnection_cost = config.target_capacity_mw * 100_000

        # Rough CAPEX estimate
        capex_per_mw = 1_000_000  # $1M/MW DC
        report.estimated_capex = report.recommended_capacity_mw * capex_per_mw + interconnection_cost

        # LCOE estimate (simplified)
        capacity_factor = 0.25
        annual_gen_mwh = report.recommended_capacity_mw * 8760 * capacity_factor
        annual_opex = report.recommended_capacity_mw * 15_000  # $15k/MW/yr
        lifetime_years = 25

        total_gen = annual_gen_mwh * lifetime_years * 0.85  # Degradation
        total_cost = report.estimated_capex + (annual_opex * lifetime_years)
        report.estimated_lcoe = total_cost / total_gen if total_gen > 0 else 0

        # Timeline
        base_months = 24
        if permitting_result and permitting_result.data.get("public_hearing_required"):
            base_months += 6
        if grid_result:
            base_months += grid_result.data.get("cost_breakdown", {}).get("study_months", 18)

        report.estimated_timeline_months = base_months

        # Next steps
        report.next_steps = [
            "Conduct site visit and preliminary survey",
            "Engage landowner for lease discussion",
            "Submit interconnection pre-application",
            "Initiate desktop environmental review",
            "Review zoning ordinance in detail",
        ]

        return report

    async def _generate_executive_summary(
        self,
        parcel: Parcel,
        site_score: SiteScore,
        risks: list[str],
        config: SiteAnalysisConfig,
    ) -> str:
        """Generate executive summary."""
        viability = "PROCEED" if site_score.proceed_recommendation == "proceed" else \
                   "CONDITIONAL" if site_score.proceed_recommendation == "conditional" else "AVOID"

        summary = f"""SITE ANALYSIS EXECUTIVE SUMMARY
{'=' * 50}

PARCEL: {parcel.apn or parcel.id}
LOCATION: {parcel.municipality}, {parcel.county}, {parcel.state}
ACREAGE: {parcel.acreage:.1f} acres
PROJECT: {config.target_capacity_mw:.1f} MW DC {config.project_type.value}

OVERALL SCORE: {site_score.overall_score:.0f}/100
RECOMMENDATION: {viability}

COMPONENT SCORES:
- Permitting:     {site_score.permitting_score:.0f}/100
- Grid:           {site_score.grid_score:.0f}/100
- Environmental:  {site_score.environmental_score:.0f}/100
- Land:           {site_score.land_score:.0f}/100

KEY RISKS ({len(risks)}):
"""
        for risk in risks[:5]:
            summary += f"- {risk}\n"

        if site_score.fatal_flaws:
            summary += f"\nFATAL FLAWS: {len(site_score.fatal_flaws)}\n"
            for flaw in site_score.fatal_flaws:
                summary += f"- {flaw}\n"

        return summary

    async def analyze_multiple_parcels(
        self,
        parcels: list[Parcel],
        config: SiteAnalysisConfig = None,
    ) -> list[AgentResult]:
        """Analyze multiple parcels and rank them."""
        config = config or SiteAnalysisConfig()

        # Analyze all parcels concurrently
        tasks = [self.execute(parcel, config=config) for parcel in parcels]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results and sort by score
        successful = [
            r for r in results
            if isinstance(r, AgentResult) and r.success
        ]

        successful.sort(
            key=lambda r: r.data.get("site_score", {}).get("overall_score", 0),
            reverse=True,
        )

        return successful
