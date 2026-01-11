"""
TerraJinki Permitting Swarm

Multi-agent system for zoning ordinance analysis using RAG+
(Retrieval-Augmented Generation with Application-Aware Reasoning).

Agents:
- ZoningParserAgent: Extracts solar permissions from ordinance text
- SetbackAnalyzerAgent: Calculates buildable area after setbacks
- VariancePredictorAgent: Predicts variance approval probability
- TimelineEstimatorAgent: Estimates permit approval timeline
- MoratoriumMonitorAgent: Tracks moratorium status and expiration
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, List, Any
from uuid import uuid4
import asyncio
import json
import logging
import re

from terrajinki.core.types import (
    Parcel,
    Jurisdiction,
    SolarPermission,
    ZoningType,
    AgentResult,
    SwarmResult,
    AgentStatus,
)
from terrajinki.agents.base import (
    BaseAgent,
    AgentContext,
    CompositeAgent,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PERMITTING AGENTS
# =============================================================================

class ZoningParserAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """
    Parses zoning ordinances to extract solar development permissions.

    Uses RAG+ to:
    1. Retrieve relevant sections from ordinance corpus
    2. Apply structured extraction prompts
    3. Cross-reference with state-level preemption laws
    """

    name = "zoning_parser"
    description = "Extracts solar permissions and requirements from zoning ordinances"
    model_tier = "analysis"

    # Prompt template for ordinance analysis
    ANALYSIS_PROMPT = """Analyze this zoning ordinance text and extract solar development permissions.

JURISDICTION: {jurisdiction_name}
ZONING DISTRICT: {zoning_code} ({zoning_type})
PARCEL SIZE: {acreage} acres

ORDINANCE TEXT:
{ordinance_text}

Extract the following information:
1. Is utility-scale solar explicitly permitted, conditional, or prohibited in this zone?
2. What permits/approvals are required?
3. What are the setback requirements (property line, road, residential)?
4. Are there height restrictions?
5. Is screening/buffering required?
6. Is a decommissioning plan/bond required?
7. Are there any acreage limits or caps?
8. Is there an active moratorium?

Respond in JSON format:
{{
    "solar_permission": "by_right|conditional_use|special_exception|variance_required|prohibited|moratorium|unknown",
    "confidence": 0.0-1.0,
    "permits_required": ["list of required permits"],
    "setbacks": {{
        "property_line_ft": 0,
        "road_ft": 0,
        "residential_ft": 0,
        "structure_ft": 0
    }},
    "height_limit_ft": 0,
    "screening_required": true/false,
    "screening_requirements": "description if required",
    "decommissioning_required": true/false,
    "decommissioning_bond_pct": 0,
    "acreage_cap": 0,
    "moratorium_active": true/false,
    "moratorium_expiration": "YYYY-MM-DD or null",
    "key_provisions": ["list of key ordinance provisions"],
    "citations": ["section numbers referenced"],
    "ambiguities": ["any unclear provisions"],
    "state_preemption_applies": true/false
}}"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse zoning ordinance and extract permissions."""
        parcel = input_data.get("parcel")
        jurisdiction = input_data.get("jurisdiction")
        ordinance_text = input_data.get("ordinance_text", "")

        if not ordinance_text:
            # Try to retrieve ordinance from RAG
            ordinance_text = await self._retrieve_ordinance(jurisdiction)

        if not ordinance_text:
            # Return unknown status if no ordinance available
            return {
                "solar_permission": SolarPermission.UNKNOWN.value,
                "confidence": 0.2,
                "permits_required": [],
                "notes": "No ordinance text available for analysis",
            }

        prompt = self.ANALYSIS_PROMPT.format(
            jurisdiction_name=jurisdiction.name if jurisdiction else parcel.municipality,
            zoning_code=parcel.zoning_code,
            zoning_type=parcel.zoning_type.value if parcel.zoning_type else "unknown",
            acreage=parcel.acreage,
            ordinance_text=ordinance_text[:15000],  # Limit context length
        )

        result = await self.call_llm(prompt, json_mode=True)

        # Validate and normalize permission
        permission_str = result.get("solar_permission", "unknown")
        try:
            permission = SolarPermission(permission_str)
        except ValueError:
            permission = SolarPermission.UNKNOWN

        result["solar_permission"] = permission.value
        result["score"] = self._calculate_permitting_score(result)

        return result

    async def _retrieve_ordinance(self, jurisdiction: Optional[Jurisdiction]) -> str:
        """Retrieve ordinance text from RAG corpus."""
        # In production, this would query Qdrant/vector store
        # For now, return placeholder
        if jurisdiction and jurisdiction.solar_ordinance_text:
            return jurisdiction.solar_ordinance_text

        return ""

    def _calculate_permitting_score(self, result: Dict[str, Any]) -> float:
        """Calculate permitting score based on analysis."""
        permission = result.get("solar_permission", "unknown")

        base_scores = {
            "by_right": 100,
            "conditional_use": 75,
            "special_exception": 60,
            "variance_required": 40,
            "under_review": 50,
            "moratorium": 10,
            "prohibited": 0,
            "unknown": 30,
        }

        score = base_scores.get(permission, 30)

        # Adjust for complexity
        if len(result.get("permits_required", [])) > 3:
            score -= 5

        if result.get("decommissioning_required"):
            score -= 2

        if result.get("moratorium_active"):
            score = min(score, 20)

        # Adjust for confidence
        confidence = result.get("confidence", 0.5)
        score = score * (0.5 + 0.5 * confidence)

        return max(0, min(100, score))


class SetbackAnalyzerAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """
    Calculates buildable area after applying setback requirements.

    Uses parcel geometry and setback rules to determine actual
    developable acreage.
    """

    name = "setback_analyzer"
    description = "Calculates buildable area after setback requirements"
    model_tier = "fast"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate buildable area after setbacks."""
        parcel = input_data.get("parcel")
        setbacks = input_data.get("setbacks", {})

        # Default setbacks if not specified
        property_line_ft = setbacks.get("property_line_ft", 50)
        road_ft = setbacks.get("road_ft", 100)
        residential_ft = setbacks.get("residential_ft", 200)

        # Simplified calculation - real implementation would use PostGIS
        total_acres = parcel.acreage
        road_frontage_ft = parcel.road_frontage_ft or 500

        # Estimate setback area
        avg_setback_ft = (property_line_ft + road_ft) / 2
        # Assume roughly square parcel
        parcel_side_ft = (total_acres * 43560) ** 0.5

        # Subtract setback buffer
        buildable_side_ft = max(0, parcel_side_ft - 2 * avg_setback_ft)
        buildable_acres = (buildable_side_ft ** 2) / 43560

        # Apply residential buffer if neighbors are residential
        # (simplified - would check actual adjacencies)
        if residential_ft > property_line_ft:
            buildable_acres *= 0.85

        buildable_pct = (buildable_acres / total_acres * 100) if total_acres > 0 else 0

        return {
            "total_acres": total_acres,
            "buildable_acres": round(buildable_acres, 2),
            "buildable_pct": round(buildable_pct, 1),
            "setbacks_applied": {
                "property_line_ft": property_line_ft,
                "road_ft": road_ft,
                "residential_ft": residential_ft,
            },
            "estimated_capacity_mw": round(buildable_acres / 6, 2),  # ~6 acres/MW
            "score": min(100, buildable_pct * 1.5),  # Score based on usable area
        }


class VariancePredictorAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """
    Predicts probability of variance/exception approval.

    Analyzes historical approval patterns and current political
    climate to estimate likelihood of success.
    """

    name = "variance_predictor"
    description = "Predicts variance approval probability"
    model_tier = "analysis"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict variance approval probability."""
        jurisdiction = input_data.get("jurisdiction")
        parcel = input_data.get("parcel")
        variance_type = input_data.get("variance_type", "conditional_use")

        prompt = f"""Estimate the probability of variance/permit approval for this solar project.

JURISDICTION: {jurisdiction.name if jurisdiction else parcel.municipality}
VARIANCE TYPE: {variance_type}
PARCEL SIZE: {parcel.acreage} acres

HISTORICAL DATA (if available):
- Permits approved last year: {jurisdiction.permits_approved_last_year if jurisdiction else 'unknown'}
- Permits denied last year: {jurisdiction.permits_denied_last_year if jurisdiction else 'unknown'}
- Avg approval time: {jurisdiction.avg_approval_days if jurisdiction else 'unknown'} days

Consider:
1. Historical approval rates
2. Project size relative to local norms
3. General solar policy trends
4. Potential community opposition factors

Respond in JSON:
{{
    "approval_probability": 0.0-1.0,
    "confidence": 0.0-1.0,
    "favorable_factors": ["list"],
    "risk_factors": ["list"],
    "recommended_mitigation": ["list"],
    "estimated_timeline_days": 0,
    "estimated_cost": 0
}}"""

        result = await self.call_llm(prompt, json_mode=True)
        result["score"] = result.get("approval_probability", 0.5) * 100

        return result


class TimelineEstimatorAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """
    Estimates permit approval timeline.

    Considers jurisdiction processing times, required reviews,
    and public hearing schedules.
    """

    name = "timeline_estimator"
    description = "Estimates permit approval timeline"
    model_tier = "fast"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate permitting timeline."""
        jurisdiction = input_data.get("jurisdiction")
        permit_type = input_data.get("permit_type", "conditional_use")
        permits_required = input_data.get("permits_required", [])

        # Base timelines by permit type
        base_days = {
            "by_right": 30,
            "conditional_use": 90,
            "special_exception": 120,
            "variance": 180,
            "rezoning": 240,
        }

        base = base_days.get(permit_type, 90)

        # Add time for additional permits
        additional_days = len(permits_required) * 15

        # Use historical average if available
        if jurisdiction and jurisdiction.avg_approval_days > 0:
            estimated_days = (base + jurisdiction.avg_approval_days) / 2 + additional_days
        else:
            estimated_days = base + additional_days

        # Add buffer for public hearings (typically monthly)
        if permit_type in ["conditional_use", "special_exception", "variance"]:
            estimated_days += 30  # Assume 1 hearing cycle

        return {
            "permit_type": permit_type,
            "estimated_days": round(estimated_days),
            "estimated_months": round(estimated_days / 30, 1),
            "confidence": 0.7,
            "milestones": [
                {"name": "Application submission", "days": 0},
                {"name": "Completeness review", "days": 14},
                {"name": "Staff review", "days": 45},
                {"name": "Public hearing", "days": 75},
                {"name": "Decision", "days": round(estimated_days)},
            ],
            "score": max(0, 100 - (estimated_days / 3)),  # Faster = better
        }


class MoratoriumMonitorAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """
    Monitors moratorium status and tracks expiration dates.

    Alerts on jurisdictions with active or pending moratoriums.
    """

    name = "moratorium_monitor"
    description = "Tracks moratorium status and expiration"
    model_tier = "fast"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check moratorium status."""
        jurisdiction = input_data.get("jurisdiction")
        parcel = input_data.get("parcel")

        # In production, this would check a real database
        # For now, simulate based on jurisdiction data
        moratorium_active = False
        moratorium_expiration = None

        if jurisdiction:
            if jurisdiction.utility_solar_permission == SolarPermission.MORATORIUM:
                moratorium_active = True
                # Estimate expiration (typically 6-12 months)
                moratorium_expiration = "2026-06-01"

        return {
            "moratorium_active": moratorium_active,
            "moratorium_expiration": moratorium_expiration,
            "moratorium_type": "utility_solar" if moratorium_active else None,
            "days_until_expiration": 180 if moratorium_active else None,
            "likelihood_of_extension": 0.3 if moratorium_active else 0.0,
            "score": 0 if moratorium_active else 100,
            "recommendation": "Wait for expiration or seek variance" if moratorium_active else "Proceed",
        }


# =============================================================================
# PERMITTING SWARM
# =============================================================================

class PermittingSwarm(CompositeAgent[Dict[str, Any], SwarmResult]):
    """
    Coordinated swarm for comprehensive permitting analysis.

    Runs multiple specialized agents to provide complete
    permitting risk assessment with RAG+ ordinance analysis.
    """

    name = "permitting_swarm"
    description = "Comprehensive permitting and zoning analysis"

    def __init__(self, context: Optional[AgentContext] = None):
        super().__init__(context)
        self._agents = {
            "zoning_parser": ZoningParserAgent(context),
            "setback_analyzer": SetbackAnalyzerAgent(context),
            "variance_predictor": VariancePredictorAgent(context),
            "timeline_estimator": TimelineEstimatorAgent(context),
            "moratorium_monitor": MoratoriumMonitorAgent(context),
        }

    async def execute(self, input_data: Dict[str, Any]) -> SwarmResult:
        """Execute comprehensive permitting analysis."""
        start_time = datetime.utcnow()
        parcel = input_data.get("parcel") if isinstance(input_data, dict) else input_data.parcel
        jurisdiction = input_data.get("jurisdiction") if isinstance(input_data, dict) else None

        result = SwarmResult(
            swarm_id=str(uuid4()),
            swarm_type="permitting",
            started_at=start_time,
        )

        try:
            # Step 1: Check moratorium first
            moratorium_result = await self._agents["moratorium_monitor"].run({
                "parcel": parcel,
                "jurisdiction": jurisdiction,
            })
            result.agent_results.append(moratorium_result)

            # Step 2: Parse zoning ordinance
            zoning_result = await self._agents["zoning_parser"].run({
                "parcel": parcel,
                "jurisdiction": jurisdiction,
            })
            result.agent_results.append(zoning_result)

            # Step 3: Analyze setbacks (depends on zoning result)
            setbacks = zoning_result.output.get("setbacks", {})
            setback_result = await self._agents["setback_analyzer"].run({
                "parcel": parcel,
                "setbacks": setbacks,
            })
            result.agent_results.append(setback_result)

            # Step 4 & 5: Variance and timeline in parallel
            variance_task = asyncio.create_task(
                self._agents["variance_predictor"].run({
                    "parcel": parcel,
                    "jurisdiction": jurisdiction,
                    "variance_type": zoning_result.output.get("solar_permission", "conditional_use"),
                })
            )

            timeline_task = asyncio.create_task(
                self._agents["timeline_estimator"].run({
                    "parcel": parcel,
                    "jurisdiction": jurisdiction,
                    "permit_type": zoning_result.output.get("solar_permission", "conditional_use"),
                    "permits_required": zoning_result.output.get("permits_required", []),
                })
            )

            variance_result, timeline_result = await asyncio.gather(
                variance_task, timeline_task
            )
            result.agent_results.extend([variance_result, timeline_result])

            # Aggregate results
            result = self._aggregate_results(result)
            result.status = AgentStatus.COMPLETED

        except Exception as e:
            logger.exception(f"Permitting swarm failed: {e}")
            result.status = AgentStatus.FAILED
            result.key_findings.append(f"Error: {str(e)}")

        result.completed_at = datetime.utcnow()
        return result

    def _aggregate_results(self, result: SwarmResult) -> SwarmResult:
        """Aggregate individual agent results into swarm summary."""
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
                    # Extract key findings
                    if output.get("solar_permission"):
                        findings.append(f"Solar permission: {output['solar_permission']}")

                    if output.get("buildable_acres"):
                        findings.append(f"Buildable area: {output['buildable_acres']} acres")

                    if output.get("moratorium_active"):
                        risks.append("Active moratorium in effect")
                        findings.append("MORATORIUM: Development currently prohibited")

                    if output.get("risk_factors"):
                        risks.extend(output["risk_factors"])

                    if output.get("recommended_mitigation"):
                        recommendations.extend(output["recommended_mitigation"])

        # Calculate overall score
        result.overall_score = sum(scores) / len(scores) if scores else 50
        result.confidence = 0.8  # Based on data quality

        result.key_findings = findings[:10]
        result.risks = risks[:5]
        result.recommendations = recommendations[:5]

        # Count tokens
        for agent_result in result.agent_results:
            result.total_tokens += agent_result.tokens_input + agent_result.tokens_output
            result.total_cost += agent_result.llm_cost

        return result
