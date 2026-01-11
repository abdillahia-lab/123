"""
Environmental Agent - AI-powered environmental constraint screening.

Analyzes:
- Wetlands (NWI data)
- Flood zones (FEMA)
- Endangered species habitat
- Cultural/historic resources
- Prime farmland
- Protected lands
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from loguru import logger

from paces.agents.base import BaseAgent, AgentResult
from paces.core.types import (
    Parcel,
    EnvironmentalConstraint,
    EnvironmentalScreening,
    EnvironmentalRisk,
)


class EnvironmentalAgent(BaseAgent):
    """
    AI-powered environmental screening agent.

    Capabilities:
    - Screen parcels against environmental databases
    - Identify wetlands, flood zones, endangered species habitat
    - Assess cultural and historic resources
    - Evaluate prime farmland impacts
    - Calculate environmental risk scores
    - Generate mitigation recommendations
    """

    def __init__(self):
        super().__init__(
            name="EnvironmentalAgent",
            model="claude-3-5-sonnet-20241022",
            temperature=0.1,
        )

    async def execute(
        self,
        parcel: Parcel,
        detailed_analysis: bool = False,
    ) -> AgentResult:
        """
        Screen parcel for environmental constraints.

        Args:
            parcel: Parcel to screen
            detailed_analysis: Whether to perform detailed AI analysis

        Returns:
            AgentResult with environmental screening
        """
        start_time = datetime.now()
        logger.info(f"Environmental screening for parcel {parcel.id}")

        try:
            constraints = []
            screening = EnvironmentalScreening(parcel_id=parcel.id)

            # Check wetlands
            wetland_result = await self._check_wetlands(parcel)
            if wetland_result:
                constraints.append(wetland_result)
                screening.wetlands_present = True
                screening.wetlands_acreage = wetland_result.affected_acreage

            # Check flood zones
            flood_result = await self._check_flood_zones(parcel)
            if flood_result:
                constraints.append(flood_result)
                screening.flood_zone = flood_result.description
                screening.flood_zone_acreage = flood_result.affected_acreage

            # Check endangered species
            species_result = await self._check_endangered_species(parcel)
            if species_result:
                constraints.append(species_result)
                screening.endangered_species_habitat = True
                screening.species_of_concern = species_result.description.split(", ")

            # Check cultural resources
            cultural_result = await self._check_cultural_resources(parcel)
            if cultural_result:
                constraints.append(cultural_result)
                screening.cultural_resources = True

            # Check prime farmland
            farmland_result = await self._check_prime_farmland(parcel)
            if farmland_result:
                constraints.append(farmland_result)
                screening.prime_farmland = True
                screening.prime_farmland_acreage = farmland_result.affected_acreage

            # Calculate overall risk
            screening.constraints = constraints
            screening.overall_risk = self._calculate_overall_risk(constraints)
            screening.environmental_score = self._calculate_env_score(screening)

            # Determine recommended studies
            screening.recommended_studies = self._recommend_studies(constraints)
            screening.estimated_study_cost = self._estimate_study_costs(screening.recommended_studies)

            # Generate AI summary if detailed
            if detailed_analysis:
                screening.ai_summary = await self._generate_ai_summary(parcel, screening)

            # Identify risks
            risks = [c.description for c in constraints if c.risk_level.value >= EnvironmentalRisk.MEDIUM.value]
            fatal_flaws = [c.description for c in constraints if c.is_fatal_flaw]

            recommendations = self._generate_recommendations(screening)

            return self._build_result(
                success=True,
                data={
                    "screening": screening.to_dict(),
                    "constraints": [c.to_dict() for c in constraints],
                    "environmental_score": screening.environmental_score,
                    "overall_risk": screening.overall_risk.name,
                    "recommended_studies": screening.recommended_studies,
                    "estimated_study_cost": screening.estimated_study_cost,
                },
                analysis=screening.ai_summary or self._basic_summary(screening),
                confidence=0.8,
                recommendations=recommendations,
                risks=risks if not fatal_flaws else [f"FATAL: {f}" for f in fatal_flaws] + risks,
                start_time=start_time,
            )

        except Exception as e:
            logger.error(f"Environmental screening failed: {e}")
            return self._build_result(
                success=False,
                error=str(e),
                start_time=start_time,
            )

    async def _check_wetlands(self, parcel: Parcel) -> Optional[EnvironmentalConstraint]:
        """Check for wetlands using NWI data."""
        # In production, would query NWI database/API
        # Simulate check based on parcel characteristics

        # Mock: 15% chance of wetlands on agricultural land
        import random
        if parcel.zoning_type.value == "agricultural" and random.random() < 0.15:
            affected = parcel.acreage * random.uniform(0.05, 0.25)
            return EnvironmentalConstraint(
                parcel_id=parcel.id,
                constraint_type="wetlands",
                description=f"Wetlands identified: {affected:.1f} acres of freshwater emergent wetland",
                affected_acreage=affected,
                affected_percentage=(affected / parcel.acreage) * 100,
                risk_level=EnvironmentalRisk.MEDIUM if affected < 2 else EnvironmentalRisk.HIGH,
                is_fatal_flaw=affected > parcel.acreage * 0.5,
                mitigation_possible=True,
                estimated_mitigation_cost=affected * 75_000,  # $75k/acre mitigation
                mitigation_timeline_months=12,
                data_source="NWI",
                regulation="Clean Water Act Section 404",
            )
        return None

    async def _check_flood_zones(self, parcel: Parcel) -> Optional[EnvironmentalConstraint]:
        """Check FEMA flood zones."""
        # In production, would query FEMA NFHL data
        import random

        # Mock: 10% chance of flood zone
        if random.random() < 0.10:
            zones = ["A", "AE", "X500"]
            zone = random.choice(zones)
            affected = parcel.acreage * random.uniform(0.1, 0.4)

            risk = EnvironmentalRisk.LOW
            if zone in ["A", "AE"]:
                risk = EnvironmentalRisk.HIGH

            return EnvironmentalConstraint(
                parcel_id=parcel.id,
                constraint_type="flood_zone",
                description=f"FEMA Flood Zone {zone}: {affected:.1f} acres",
                affected_acreage=affected,
                affected_percentage=(affected / parcel.acreage) * 100,
                risk_level=risk,
                is_fatal_flaw=False,  # Solar can be built in flood zones with proper design
                mitigation_possible=True,
                estimated_mitigation_cost=affected * 10_000,
                mitigation_timeline_months=3,
                data_source="FEMA NFHL",
                regulation="National Flood Insurance Program",
            )
        return None

    async def _check_endangered_species(self, parcel: Parcel) -> Optional[EnvironmentalConstraint]:
        """Check for endangered species habitat."""
        # In production, would query USFWS IPaC
        import random

        if random.random() < 0.08:
            species = ["Indiana Bat", "Northern Long-eared Bat", "Eastern Massasauga"]
            affected_species = random.sample(species, random.randint(1, 2))

            return EnvironmentalConstraint(
                parcel_id=parcel.id,
                constraint_type="endangered_species",
                description=f"Potential habitat for: {', '.join(affected_species)}",
                affected_acreage=parcel.acreage,
                affected_percentage=100,
                risk_level=EnvironmentalRisk.HIGH,
                is_fatal_flaw=False,  # Usually can be mitigated
                mitigation_possible=True,
                estimated_mitigation_cost=50_000,  # Survey + consultation
                mitigation_timeline_months=6,
                data_source="USFWS IPaC",
                regulation="Endangered Species Act",
            )
        return None

    async def _check_cultural_resources(self, parcel: Parcel) -> Optional[EnvironmentalConstraint]:
        """Check for cultural/historic resources."""
        import random

        if random.random() < 0.05:
            return EnvironmentalConstraint(
                parcel_id=parcel.id,
                constraint_type="cultural_resources",
                description="Potential archaeological sensitivity - Phase I survey recommended",
                affected_acreage=parcel.acreage,
                affected_percentage=100,
                risk_level=EnvironmentalRisk.MEDIUM,
                is_fatal_flaw=False,
                mitigation_possible=True,
                estimated_mitigation_cost=25_000,
                mitigation_timeline_months=4,
                data_source="SHPO",
                regulation="National Historic Preservation Act Section 106",
            )
        return None

    async def _check_prime_farmland(self, parcel: Parcel) -> Optional[EnvironmentalConstraint]:
        """Check for prime farmland designation."""
        # In production, would query NRCS soils data

        if parcel.zoning_type.value == "agricultural":
            import random
            if random.random() < 0.60:  # 60% of ag land is prime
                return EnvironmentalConstraint(
                    parcel_id=parcel.id,
                    constraint_type="prime_farmland",
                    description="Prime farmland soils present - may affect local approval",
                    affected_acreage=parcel.acreage * 0.8,
                    affected_percentage=80,
                    risk_level=EnvironmentalRisk.LOW,  # Usually not fatal for solar
                    is_fatal_flaw=False,
                    mitigation_possible=True,
                    estimated_mitigation_cost=0,  # Policy issue, not mitigation
                    data_source="NRCS SSURGO",
                    regulation="Farmland Protection Policy Act",
                )
        return None

    def _calculate_overall_risk(self, constraints: list[EnvironmentalConstraint]) -> EnvironmentalRisk:
        """Calculate overall environmental risk."""
        if not constraints:
            return EnvironmentalRisk.NONE

        # Check for fatal flaws
        if any(c.is_fatal_flaw for c in constraints):
            return EnvironmentalRisk.FATAL

        max_risk = max(c.risk_level.value for c in constraints)
        return EnvironmentalRisk(max_risk)

    def _calculate_env_score(self, screening: EnvironmentalScreening) -> float:
        """Calculate environmental score (0-100)."""
        score = 100.0

        for constraint in screening.constraints:
            if constraint.is_fatal_flaw:
                return 0

            # Deduct based on risk level
            deductions = {
                EnvironmentalRisk.LOW: 5,
                EnvironmentalRisk.MEDIUM: 15,
                EnvironmentalRisk.HIGH: 30,
            }
            score -= deductions.get(constraint.risk_level, 0)

        return max(0, score)

    def _recommend_studies(self, constraints: list[EnvironmentalConstraint]) -> list[str]:
        """Recommend environmental studies based on constraints."""
        studies = []

        constraint_types = {c.constraint_type for c in constraints}

        if "wetlands" in constraint_types:
            studies.append("Wetland Delineation")
            studies.append("Army Corps Pre-Application Meeting")

        if "endangered_species" in constraint_types:
            studies.append("Threatened & Endangered Species Survey")
            studies.append("USFWS Informal Consultation")

        if "cultural_resources" in constraint_types:
            studies.append("Phase I Archaeological Survey")
            studies.append("SHPO Consultation")

        if "flood_zone" in constraint_types:
            studies.append("Flood Study / Hydraulic Analysis")

        # Always recommend for utility-scale
        if not studies:
            studies.append("Desktop Environmental Review")

        return studies

    def _estimate_study_costs(self, studies: list[str]) -> float:
        """Estimate cost of recommended studies."""
        costs = {
            "Wetland Delineation": 15_000,
            "Army Corps Pre-Application Meeting": 5_000,
            "Threatened & Endangered Species Survey": 25_000,
            "USFWS Informal Consultation": 10_000,
            "Phase I Archaeological Survey": 20_000,
            "SHPO Consultation": 5_000,
            "Flood Study / Hydraulic Analysis": 15_000,
            "Desktop Environmental Review": 5_000,
        }

        return sum(costs.get(s, 10_000) for s in studies)

    async def _generate_ai_summary(
        self,
        parcel: Parcel,
        screening: EnvironmentalScreening,
    ) -> str:
        """Generate AI-powered summary of environmental findings."""
        return self._basic_summary(screening)

    def _basic_summary(self, screening: EnvironmentalScreening) -> str:
        """Generate basic summary."""
        parts = [f"Environmental Screening Summary:"]
        parts.append(f"- Overall Risk: {screening.overall_risk.name}")
        parts.append(f"- Environmental Score: {screening.environmental_score:.0f}/100")
        parts.append(f"- Constraints Found: {len(screening.constraints)}")

        if screening.wetlands_present:
            parts.append(f"- Wetlands: {screening.wetlands_acreage:.1f} acres")
        if screening.flood_zone:
            parts.append(f"- Flood Zone: {screening.flood_zone}")
        if screening.endangered_species_habitat:
            parts.append(f"- Endangered Species: Yes")
        if screening.prime_farmland:
            parts.append(f"- Prime Farmland: {screening.prime_farmland_acreage:.1f} acres")

        parts.append(f"- Recommended Studies: {len(screening.recommended_studies)}")
        parts.append(f"- Estimated Study Cost: ${screening.estimated_study_cost:,.0f}")

        return "\n".join(parts)

    def _generate_recommendations(self, screening: EnvironmentalScreening) -> list[str]:
        """Generate recommendations."""
        recs = []

        if screening.wetlands_present:
            recs.append("Conduct wetland delineation early to confirm boundaries")
            recs.append("Design project to avoid wetlands if possible")

        if screening.endangered_species_habitat:
            recs.append("Conduct species surveys during appropriate season")
            recs.append("Initiate USFWS consultation early")

        if screening.overall_risk.value >= EnvironmentalRisk.MEDIUM.value:
            recs.append("Budget additional time and cost for environmental permitting")

        if not recs:
            recs.append("Site has low environmental risk - proceed with standard due diligence")

        return recs
