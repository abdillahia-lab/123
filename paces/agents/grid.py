"""
Grid Agent - AI-powered grid interconnection analysis.

Analyzes:
- Substation capacity and proximity
- Transmission line access
- Interconnection queue position
- Upgrade cost estimation
- Timeline prediction
"""

from __future__ import annotations

import math
from datetime import datetime, date
from typing import Optional

from loguru import logger

from paces.agents.base import BaseAgent, AgentResult
from paces.core.types import (
    Parcel,
    GeoPoint,
    GridConnection,
    Substation,
    TransmissionLine,
    InterconnectionQueueEntry,
    Utility,
    InterconnectionStatus,
)


class GridAgent(BaseAgent):
    """
    AI-powered grid interconnection analysis agent.

    Capabilities:
    - Find nearest substations and transmission lines
    - Analyze hosting capacity
    - Estimate interconnection costs
    - Analyze interconnection queue
    - Predict timeline and risks
    """

    def __init__(self):
        super().__init__(
            name="GridAgent",
            model="claude-3-5-sonnet-20241022",
            temperature=0.1,
        )

        # Mock substation data (in production, from database)
        self._substations: list[Substation] = []
        self._transmission_lines: list[TransmissionLine] = []
        self._queue_entries: list[InterconnectionQueueEntry] = []

    async def execute(
        self,
        parcel: Parcel,
        project_capacity_mw: float = 5.0,
        utility: Utility = None,
    ) -> AgentResult:
        """
        Analyze grid interconnection for a parcel.

        Args:
            parcel: Parcel to analyze
            project_capacity_mw: Proposed project capacity
            utility: Override utility (otherwise auto-detected)

        Returns:
            AgentResult with grid analysis
        """
        start_time = datetime.now()
        logger.info(f"Analyzing grid for parcel {parcel.id}")

        try:
            if not parcel.centroid:
                return self._build_result(
                    success=False,
                    error="Parcel has no centroid coordinates",
                    start_time=start_time,
                )

            # Find nearest substation
            nearest_sub = self._find_nearest_substation(parcel.centroid)

            # Find nearest transmission line
            nearest_tx = self._find_nearest_transmission(parcel.centroid)

            # Analyze queue for this area
            queue_analysis = self._analyze_queue(
                parcel.state,
                parcel.county,
                nearest_sub.name if nearest_sub else "",
            )

            # Estimate costs
            costs = self._estimate_costs(
                parcel.centroid,
                nearest_sub,
                nearest_tx,
                project_capacity_mw,
            )

            # Calculate grid score
            grid_score = self._calculate_grid_score(
                nearest_sub,
                nearest_tx,
                costs,
                queue_analysis,
                project_capacity_mw,
            )

            # Build GridConnection object
            grid_connection = GridConnection(
                parcel_id=parcel.id,
                nearest_substation_id=nearest_sub.id if nearest_sub else "",
                nearest_substation_name=nearest_sub.name if nearest_sub else "",
                distance_to_substation_miles=self._distance_miles(parcel.centroid, nearest_sub.location) if nearest_sub and nearest_sub.location else 0,
                nearest_transmission_voltage_kv=nearest_tx.voltage_kv if nearest_tx else 0,
                distance_to_transmission_miles=0,  # Would calculate
                hosting_capacity_mw=nearest_sub.available_capacity_mw if nearest_sub else 0,
                available_capacity_mw=nearest_sub.available_capacity_mw if nearest_sub else 0,
                utility=utility or (nearest_sub.utility if nearest_sub else Utility.OTHER),
                estimated_interconnection_cost=costs["interconnection_cost"],
                estimated_upgrade_cost=costs["upgrade_cost"],
                estimated_total_cost=costs["total_cost"],
                cost_per_mw=costs["cost_per_mw"],
                estimated_study_months=costs["study_months"],
                estimated_construction_months=costs["construction_months"],
                queue_position=queue_analysis.get("queue_position", 0),
                projects_ahead_in_queue=queue_analysis.get("projects_ahead", 0),
                queue_mw_ahead=queue_analysis.get("mw_ahead", 0),
                grid_score=grid_score,
                congestion_risk=self._assess_congestion_risk(queue_analysis),
            )

            # Generate risks and recommendations
            risks = self._identify_risks(grid_connection, project_capacity_mw)
            recommendations = self._generate_recommendations(grid_connection, risks)

            return self._build_result(
                success=True,
                data={
                    "grid_connection": grid_connection.to_dict(),
                    "nearest_substation": nearest_sub.to_dict() if nearest_sub else None,
                    "queue_analysis": queue_analysis,
                    "cost_breakdown": costs,
                    "grid_score": grid_score,
                },
                analysis=self._generate_analysis_summary(grid_connection, queue_analysis),
                confidence=0.75,
                recommendations=recommendations,
                risks=risks,
                start_time=start_time,
            )

        except Exception as e:
            logger.error(f"Grid analysis failed: {e}")
            return self._build_result(
                success=False,
                error=str(e),
                start_time=start_time,
            )

    def _find_nearest_substation(self, location: GeoPoint) -> Optional[Substation]:
        """Find nearest substation to location."""
        if not self._substations:
            # Return mock substation for demo
            return Substation(
                id="sub_001",
                name="Sample Substation",
                utility=Utility.PJM,
                location=GeoPoint(location.latitude + 0.05, location.longitude + 0.05),
                voltage_kv=138,
                total_capacity_mw=200,
                available_capacity_mw=50,
                queued_capacity_mw=75,
            )

        nearest = None
        min_distance = float('inf')

        for sub in self._substations:
            if sub.location:
                dist = location.distance_to(sub.location)
                if dist < min_distance:
                    min_distance = dist
                    nearest = sub

        return nearest

    def _find_nearest_transmission(self, location: GeoPoint) -> Optional[TransmissionLine]:
        """Find nearest transmission line."""
        if not self._transmission_lines:
            # Return mock for demo
            return TransmissionLine(
                id="tx_001",
                name="Sample 138kV Line",
                utility=Utility.PJM,
                voltage_kv=138,
                thermal_rating_mw=300,
                available_capacity_mw=100,
            )
        return None

    def _analyze_queue(
        self,
        state: str,
        county: str,
        substation: str,
    ) -> dict:
        """Analyze interconnection queue for the area."""
        # In production, would query actual queue data
        # Simulate analysis
        return {
            "queue_position": 15,
            "projects_ahead": 14,
            "mw_ahead": 450,
            "avg_study_time_months": 24,
            "withdrawal_rate_pct": 35,
            "recent_approvals": 3,
            "recent_withdrawals": 5,
            "congestion_level": "medium",
        }

    def _estimate_costs(
        self,
        location: GeoPoint,
        substation: Optional[Substation],
        transmission: Optional[TransmissionLine],
        capacity_mw: float,
    ) -> dict:
        """Estimate interconnection and upgrade costs."""
        # Base interconnection cost
        base_cost_per_mw = 50_000  # $50k/MW baseline

        # Distance factor
        distance_miles = 0
        if substation and substation.location:
            distance_miles = self._distance_miles(location, substation.location)

        # Gen-tie cost: ~$1M per mile for basic overhead
        gen_tie_cost = distance_miles * 1_000_000

        # Network upgrades (depends on capacity headroom)
        upgrade_cost = 0
        if substation:
            if capacity_mw > substation.available_capacity_mw:
                # Need upgrades
                upgrade_cost = (capacity_mw - substation.available_capacity_mw) * 150_000

        # Study costs
        study_cost = 150_000  # Feasibility + SIS + Facilities

        # Total
        interconnection_cost = (capacity_mw * base_cost_per_mw) + gen_tie_cost + study_cost
        total_cost = interconnection_cost + upgrade_cost

        return {
            "interconnection_cost": interconnection_cost,
            "upgrade_cost": upgrade_cost,
            "gen_tie_cost": gen_tie_cost,
            "study_cost": study_cost,
            "total_cost": total_cost,
            "cost_per_mw": total_cost / capacity_mw if capacity_mw > 0 else 0,
            "distance_miles": distance_miles,
            "study_months": 18,
            "construction_months": 12,
        }

    def _calculate_grid_score(
        self,
        substation: Optional[Substation],
        transmission: Optional[TransmissionLine],
        costs: dict,
        queue_analysis: dict,
        capacity_mw: float,
    ) -> float:
        """Calculate grid viability score (0-100)."""
        score = 100.0

        # Distance penalty
        distance = costs.get("distance_miles", 0)
        if distance > 10:
            score -= 30
        elif distance > 5:
            score -= 15
        elif distance > 2:
            score -= 5

        # Capacity availability
        if substation:
            if capacity_mw > substation.available_capacity_mw:
                # Need upgrades
                shortage_pct = (capacity_mw - substation.available_capacity_mw) / capacity_mw
                score -= shortage_pct * 30

        # Queue congestion
        congestion = queue_analysis.get("congestion_level", "medium")
        if congestion == "high":
            score -= 25
        elif congestion == "medium":
            score -= 10

        # Cost penalty
        cost_per_mw = costs.get("cost_per_mw", 0)
        if cost_per_mw > 200_000:
            score -= 20
        elif cost_per_mw > 100_000:
            score -= 10

        return max(0, min(100, score))

    def _assess_congestion_risk(self, queue_analysis: dict) -> str:
        """Assess congestion risk level."""
        mw_ahead = queue_analysis.get("mw_ahead", 0)
        if mw_ahead > 500:
            return "high"
        elif mw_ahead > 200:
            return "medium"
        return "low"

    def _distance_miles(self, p1: GeoPoint, p2: GeoPoint) -> float:
        """Calculate distance in miles."""
        km = p1.distance_to(p2)
        return km * 0.621371

    def _identify_risks(
        self,
        connection: GridConnection,
        capacity_mw: float,
    ) -> list[str]:
        """Identify grid-related risks."""
        risks = []

        if connection.distance_to_substation_miles > 5:
            risks.append(f"Long gen-tie required: {connection.distance_to_substation_miles:.1f} miles to substation")

        if connection.available_capacity_mw < capacity_mw:
            risks.append(f"Insufficient hosting capacity: {connection.available_capacity_mw:.1f} MW available vs {capacity_mw:.1f} MW requested")

        if connection.queue_mw_ahead > 300:
            risks.append(f"High queue congestion: {connection.queue_mw_ahead:.0f} MW ahead in queue")

        if connection.estimated_total_cost > capacity_mw * 150_000:
            risks.append(f"High interconnection cost: ${connection.estimated_total_cost:,.0f} (${connection.cost_per_mw:,.0f}/MW)")

        if connection.congestion_risk == "high":
            risks.append("High grid congestion may delay interconnection")

        return risks

    def _generate_recommendations(
        self,
        connection: GridConnection,
        risks: list[str],
    ) -> list[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        if connection.distance_to_substation_miles > 3:
            recommendations.append("Consider co-locating with nearby queued projects to share gen-tie costs")

        if connection.queue_mw_ahead > 200:
            recommendations.append("Monitor queue withdrawals - many projects ahead may withdraw")

        if connection.available_capacity_mw < 10:
            recommendations.append("Investigate nearby substations for better capacity")

        recommendations.append("Engage with utility early for pre-application meeting")
        recommendations.append("Consider phased development to match available capacity")

        return recommendations

    def _generate_analysis_summary(
        self,
        connection: GridConnection,
        queue_analysis: dict,
    ) -> str:
        """Generate analysis summary."""
        return f"""Grid Analysis Summary:
- Nearest substation: {connection.nearest_substation_name} ({connection.distance_to_substation_miles:.1f} miles)
- Available capacity: {connection.available_capacity_mw:.1f} MW
- Queue position: {connection.queue_position} ({connection.queue_mw_ahead:.0f} MW ahead)
- Estimated cost: ${connection.estimated_total_cost:,.0f} (${connection.cost_per_mw:,.0f}/MW)
- Grid score: {connection.grid_score:.0f}/100
- Congestion risk: {connection.congestion_risk}"""
