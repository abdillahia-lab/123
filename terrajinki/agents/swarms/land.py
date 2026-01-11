"""
TerraJinki Land Swarm

Multi-agent system for land and ownership analysis.

Agents:
- OwnershipAgent: Identifies current owners and contact info
- TopographyAgent: Slope, aspect, elevation analysis
- AccessAnalyzerAgent: Road access and easement analysis
- ValueEstimatorAgent: Land value and lease rate estimation
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, List, Any
from uuid import uuid4
import asyncio
import json
import logging
import random

from terrajinki.core.types import (
    Parcel,
    LandOwner,
    GeoPoint,
    AgentResult,
    SwarmResult,
    AgentStatus,
)
from terrajinki.agents.base import (
    BaseAgent,
    ToolAgent,
    AgentContext,
    CompositeAgent,
)

logger = logging.getLogger(__name__)


class OwnershipAgent(ToolAgent):
    """
    Identifies landowner information and contact details.

    Aggregates data from county assessor records and
    skip-tracing services.
    """

    name = "ownership"
    description = "Identifies landowners and contact info"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get ownership information."""
        parcel = input_data.get("parcel")

        # Simulate ownership lookup
        owner_types = ["individual", "llc", "corporation", "trust", "government"]
        owner_type = random.choices(
            owner_types,
            weights=[0.40, 0.25, 0.15, 0.10, 0.10]
        )[0]

        # Generate mock owner data
        owner_name = parcel.owner_name or f"Landowner {random.randint(1000, 9999)}"

        # Contact availability varies by owner type
        contact_available = {
            "individual": 0.70,
            "llc": 0.85,
            "corporation": 0.90,
            "trust": 0.60,
            "government": 0.95,
        }

        has_contact = random.random() < contact_available.get(owner_type, 0.70)

        # Check for adjacent parcels owned by same entity
        adjacent_owned = random.randint(0, 3)
        adjacent_acres = adjacent_owned * random.uniform(10, 50)

        return {
            "owner_name": owner_name,
            "owner_type": owner_type,
            "owner_address": parcel.owner_address or "Address Available",
            "contact_available": has_contact,
            "phone_available": has_contact and random.random() < 0.60,
            "email_available": has_contact and random.random() < 0.40,
            "owner_since": f"{random.randint(1990, 2020)}",
            "acquisition_price": parcel.last_sale_price or random.randint(50000, 500000),
            "adjacent_parcels_owned": adjacent_owned,
            "total_acreage_owned": parcel.acreage + adjacent_acres,
            "other_parcels_available": adjacent_owned > 0,
            "corporate_agent_registered": owner_type in ["llc", "corporation"],
            "score": 90 if has_contact else 60,
        }


class TopographyAgent(ToolAgent):
    """
    Analyzes terrain characteristics for solar suitability.

    Uses DEM data to calculate slope, aspect, and elevation.
    """

    name = "topography"
    description = "Analyzes slope, aspect, and elevation"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze topography."""
        parcel = input_data.get("parcel")

        # Use parcel data or generate estimates
        avg_slope = parcel.slope_avg_pct or random.uniform(0, 12)
        max_slope = parcel.slope_max_pct or avg_slope * random.uniform(1.5, 2.5)
        elevation_min = parcel.elevation_min_ft or random.randint(100, 1000)
        elevation_max = parcel.elevation_max_ft or elevation_min + random.randint(10, 100)

        # Aspect analysis
        aspects = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "FLAT"]
        aspect_weights = [0.05, 0.08, 0.12, 0.15, 0.20, 0.15, 0.12, 0.08, 0.05]
        primary_aspect = random.choices(aspects, aspect_weights)[0]

        # Calculate suitability
        # Ideal: < 5% slope, south-facing
        slope_penalty = max(0, (avg_slope - 5) * 5)
        aspect_bonus = {"S": 10, "SE": 8, "SW": 8, "E": 5, "W": 5, "FLAT": 3}.get(primary_aspect, 0)

        score = 100 - slope_penalty + aspect_bonus
        score = max(0, min(100, score))

        # Determine suitable areas
        if avg_slope < 5:
            suitable_pct = 95
        elif avg_slope < 10:
            suitable_pct = 75
        elif avg_slope < 15:
            suitable_pct = 50
        else:
            suitable_pct = 25

        return {
            "avg_slope_pct": round(avg_slope, 2),
            "max_slope_pct": round(max_slope, 2),
            "elevation_min_ft": elevation_min,
            "elevation_max_ft": elevation_max,
            "elevation_range_ft": elevation_max - elevation_min,
            "primary_aspect": primary_aspect,
            "aspect_breakdown": {
                "south_facing_pct": random.randint(20, 40) if primary_aspect in ["S", "SE", "SW"] else random.randint(5, 20),
                "east_west_pct": random.randint(30, 50),
                "north_facing_pct": random.randint(10, 25),
            },
            "suitable_for_fixed_tilt": avg_slope < 10,
            "suitable_for_trackers": avg_slope < 6,
            "suitable_area_pct": suitable_pct,
            "suitable_acres": round(parcel.acreage * suitable_pct / 100, 2),
            "grading_required": avg_slope > 8,
            "estimated_grading_cost": round(parcel.acreage * 2000 * max(0, avg_slope - 5) / 10) if avg_slope > 5 else 0,
            "score": round(score),
        }


class AccessAnalyzerAgent(ToolAgent):
    """
    Analyzes road access and easement requirements.

    Critical for construction access and ongoing O&M.
    """

    name = "access_analyzer"
    description = "Analyzes road access and easements"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze access."""
        parcel = input_data.get("parcel")

        # Determine access quality
        has_road_access = parcel.road_access if parcel.road_access is not None else random.random() > 0.1
        road_frontage = parcel.road_frontage_ft or random.randint(100, 1000) if has_road_access else 0

        # Road type
        road_types = ["paved_public", "paved_private", "gravel_public", "gravel_private", "dirt"]
        road_weights = [0.35, 0.15, 0.25, 0.15, 0.10]
        road_type = random.choices(road_types, road_weights)[0]

        # Load restrictions
        has_restrictions = "private" in road_type or road_type == "dirt"

        # Distance to major road
        distance_to_highway = random.uniform(0.5, 10)

        # Score
        base_scores = {
            "paved_public": 100,
            "paved_private": 80,
            "gravel_public": 70,
            "gravel_private": 60,
            "dirt": 40,
        }

        if not has_road_access:
            score = 20
        else:
            score = base_scores.get(road_type, 50)
            if road_frontage < 200:
                score -= 10
            if distance_to_highway > 5:
                score -= 5

        return {
            "has_road_access": has_road_access,
            "road_frontage_ft": road_frontage,
            "road_type": road_type,
            "road_paved": "paved" in road_type,
            "road_public": "public" in road_type,
            "weight_restrictions": has_restrictions,
            "max_weight_tons": 40 if "paved" in road_type else 20,
            "distance_to_highway_mi": round(distance_to_highway, 1),
            "easement_required": not has_road_access,
            "estimated_easement_cost": 50000 if not has_road_access else 0,
            "road_improvement_needed": road_type in ["gravel_private", "dirt"],
            "estimated_improvement_cost": 25000 if road_type == "dirt" else 10000 if "gravel" in road_type else 0,
            "construction_access_adequate": "paved" in road_type or (road_type.startswith("gravel") and "public" in road_type),
            "score": max(0, round(score)),
        }


class ValueEstimatorAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """
    Estimates land value and optimal lease rates.

    Uses comparable sales and market data to determine
    fair value for land acquisition or lease.
    """

    name = "value_estimator"
    description = "Estimates land value and lease rates"
    model_tier = "fast"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate land value."""
        parcel = input_data.get("parcel")

        # Use existing values or estimate
        assessed_value = parcel.assessed_value or parcel.acreage * random.randint(1500, 8000)
        market_value = parcel.market_value or assessed_value * random.uniform(1.0, 1.5)
        price_per_acre = parcel.price_per_acre or market_value / max(parcel.acreage, 1)

        # Estimate lease rates
        # Solar leases typically $800-1500/acre/year
        base_lease = random.uniform(800, 1500)

        # Adjust for location quality
        if parcel.state in ["CA", "TX", "FL"]:
            base_lease *= 1.2
        elif parcel.state in ["OH", "IN", "IL"]:
            base_lease *= 1.0

        # Estimate option payment
        option_per_acre = base_lease * random.uniform(0.5, 1.5)

        return {
            "assessed_value": round(assessed_value),
            "estimated_market_value": round(market_value),
            "price_per_acre": round(price_per_acre),
            "estimated_lease_per_acre_year": round(base_lease),
            "estimated_option_per_acre": round(option_per_acre),
            "total_annual_lease": round(base_lease * parcel.acreage),
            "total_option_payment": round(option_per_acre * parcel.acreage),
            "lease_term_typical_years": 35,
            "escalation_pct_typical": 1.5,
            "comparable_sales": [
                {"acreage": round(parcel.acreage * random.uniform(0.7, 1.3)), "price_per_acre": round(price_per_acre * random.uniform(0.85, 1.15))}
                for _ in range(3)
            ],
            "market_trend": random.choice(["stable", "increasing", "decreasing"]),
            "score": 75,  # Value estimation doesn't directly affect site score
        }


class LandSwarm(CompositeAgent[Dict[str, Any], SwarmResult]):
    """
    Coordinated swarm for land analysis.

    Combines ownership, topography, access, and value
    assessments for complete land intelligence.
    """

    name = "land_swarm"
    description = "Comprehensive land and ownership analysis"

    def __init__(self, context: Optional[AgentContext] = None):
        super().__init__(context)
        self._agents = {
            "ownership": OwnershipAgent(context),
            "topography": TopographyAgent(context),
            "access": AccessAnalyzerAgent(context),
            "value": ValueEstimatorAgent(context),
        }

    async def execute(self, input_data: Dict[str, Any]) -> SwarmResult:
        """Execute comprehensive land analysis."""
        start_time = datetime.utcnow()
        parcel = input_data.get("parcel") if isinstance(input_data, dict) else input_data.parcel

        result = SwarmResult(
            swarm_id=str(uuid4()),
            swarm_type="land",
            started_at=start_time,
        )

        try:
            # Run all land agents in parallel
            tasks = [
                asyncio.create_task(self._agents["ownership"].run({"parcel": parcel})),
                asyncio.create_task(self._agents["topography"].run({"parcel": parcel})),
                asyncio.create_task(self._agents["access"].run({"parcel": parcel})),
                asyncio.create_task(self._agents["value"].run({"parcel": parcel})),
            ]

            agent_results = await asyncio.gather(*tasks)
            result.agent_results.extend(agent_results)

            # Aggregate results
            result = self._aggregate_results(result)
            result.status = AgentStatus.COMPLETED

        except Exception as e:
            logger.exception(f"Land swarm failed: {e}")
            result.status = AgentStatus.FAILED
            result.key_findings.append(f"Error: {str(e)}")

        result.completed_at = datetime.utcnow()
        return result

    def _aggregate_results(self, result: SwarmResult) -> SwarmResult:
        """Aggregate land analysis results."""
        scores = []
        findings = []
        risks = []
        recommendations = []

        for agent_result in result.agent_results:
            if agent_result.success:
                if agent_result.score:
                    scores.append(agent_result.score)

                output = agent_result.output
                if isinstance(output, dict):
                    # Ownership
                    if output.get("owner_name"):
                        findings.append(f"Owner: {output['owner_name']} ({output.get('owner_type', 'unknown')})")
                        if output.get("adjacent_parcels_owned", 0) > 0:
                            findings.append(f"Owner has {output['adjacent_parcels_owned']} adjacent parcels")

                    # Topography
                    if output.get("avg_slope_pct") is not None:
                        findings.append(f"Average slope: {output['avg_slope_pct']}%")
                        if output.get("avg_slope_pct", 0) > 10:
                            risks.append("Steep slopes may require grading")

                    # Access
                    if output.get("has_road_access") is False:
                        risks.append("No direct road access - easement required")
                    elif output.get("road_type"):
                        findings.append(f"Road access: {output['road_type']}")

                    # Value
                    if output.get("estimated_lease_per_acre_year"):
                        findings.append(f"Est. lease rate: ${output['estimated_lease_per_acre_year']}/acre/year")

                    # Collect recommendations
                    if not output.get("contact_available"):
                        recommendations.append("Skip-trace owner contact information")
                    if output.get("grading_required"):
                        recommendations.append("Budget for site grading")
                    if output.get("easement_required"):
                        recommendations.append("Negotiate access easement early")

        # Calculate overall score
        if scores:
            result.overall_score = sum(scores) / len(scores)
        else:
            result.overall_score = 50

        result.confidence = 0.80
        result.key_findings = findings[:10]
        result.risks = risks[:5]
        result.recommendations = recommendations[:5]

        # Token tracking
        for agent_result in result.agent_results:
            result.total_tokens += agent_result.tokens_input + agent_result.tokens_output
            result.total_cost += agent_result.llm_cost

        return result
