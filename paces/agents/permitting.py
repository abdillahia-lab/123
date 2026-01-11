"""
Permitting Agent - LLM-powered zoning and permitting analysis.

Analyzes:
- Zoning ordinances and regulations
- Solar/renewable energy permissions
- Setback requirements
- Conditional use permit requirements
- Permitting risk scoring
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from loguru import logger

from paces.agents.base import BaseAgent, AgentResult
from paces.core.types import (
    Jurisdiction,
    Parcel,
    LandUsePermission,
    ZoningType,
)


PERMITTING_SYSTEM_PROMPT = """You are an expert renewable energy permitting analyst specializing in solar development. Your role is to analyze zoning ordinances and regulations to determine:

1. Whether utility-scale or commercial solar is permitted
2. What zoning districts allow solar development
3. What permits are required (by-right, conditional use, special exception, variance)
4. Setback requirements from property lines, roads, and structures
5. Height limitations
6. Screening and buffering requirements
7. Decommissioning requirements
8. Any moratoriums or prohibitions

Analyze the provided ordinance text and extract structured information. Be precise and cite specific sections when possible. If information is ambiguous or missing, indicate that clearly.

Always respond in valid JSON format with the following structure:
{
    "solar_permission": "by_right|conditional_use|special_exception|variance_required|prohibited|unknown",
    "permitted_zones": ["list of zoning districts where solar is allowed"],
    "prohibited_zones": ["list of zoning districts where solar is prohibited"],
    "permits_required": ["list of required permits"],
    "setbacks": {
        "property_line_ft": number or null,
        "road_ft": number or null,
        "residence_ft": number or null,
        "structure_ft": number or null
    },
    "height_limit_ft": number or null,
    "lot_coverage_max_pct": number or null,
    "screening_required": true|false,
    "decommissioning_required": true|false,
    "public_hearing_required": true|false,
    "moratorium_active": true|false,
    "key_requirements": ["list of important requirements"],
    "risks": ["list of potential permitting risks"],
    "recommendations": ["list of recommendations for developers"],
    "confidence_score": 0.0-1.0,
    "analysis_notes": "detailed analysis notes"
}"""


PERMITTING_USER_PROMPT_TEMPLATE = """Analyze the following zoning ordinance for {jurisdiction_name}, {state} to determine solar development permitting requirements:

## Ordinance Text:
{ordinance_text}

## Parcel Information:
- Zoning District: {zoning_code}
- Zoning Type: {zoning_type}
- Acreage: {acreage}
- Current Land Use: {land_use}

## Project Details:
- Project Type: {project_type}
- Proposed Capacity: {capacity_mw} MW DC
- Estimated Land Required: {land_required} acres

Please analyze the ordinance and provide:
1. Solar permission status for this zoning district
2. Required permits and approval process
3. Key requirements (setbacks, height, screening, etc.)
4. Potential risks and challenges
5. Recommendations for proceeding

Respond in valid JSON format."""


class PermittingAgent(BaseAgent):
    """
    LLM-powered permitting analysis agent.

    Capabilities:
    - Parse and analyze zoning ordinances using LLMs
    - Determine solar permission status by zone
    - Extract setback and height requirements
    - Identify permitting risks
    - Score permitting viability
    - Generate recommendations
    """

    def __init__(self):
        super().__init__(
            name="PermittingAgent",
            model="claude-3-5-sonnet-20241022",
            temperature=0.1,
            max_tokens=4096,
        )

    async def execute(
        self,
        parcel: Parcel,
        jurisdiction: Jurisdiction = None,
        ordinance_text: str = "",
        project_type: str = "utility_solar",
        capacity_mw: float = 5.0,
    ) -> AgentResult:
        """
        Analyze permitting requirements for a parcel.

        Args:
            parcel: Parcel to analyze
            jurisdiction: AHJ information
            ordinance_text: Full text of zoning ordinance
            project_type: Type of solar project
            capacity_mw: Proposed project capacity

        Returns:
            AgentResult with permitting analysis
        """
        start_time = datetime.now()
        logger.info(f"Analyzing permitting for parcel {parcel.id}")

        try:
            # Calculate land required (rough estimate: 5-7 acres per MW)
            land_required = capacity_mw * 6

            # Build the user prompt
            user_prompt = PERMITTING_USER_PROMPT_TEMPLATE.format(
                jurisdiction_name=jurisdiction.name if jurisdiction else parcel.municipality,
                state=parcel.state,
                ordinance_text=ordinance_text or "No ordinance text provided. Analyze based on general knowledge of the jurisdiction.",
                zoning_code=parcel.zoning_code,
                zoning_type=parcel.zoning_type.value,
                acreage=parcel.acreage,
                land_use=parcel.land_use_current,
                project_type=project_type,
                capacity_mw=capacity_mw,
                land_required=land_required,
            )

            # Call LLM
            response, tokens = await self._call_llm(
                PERMITTING_SYSTEM_PROMPT,
                user_prompt,
                json_mode=True,
            )

            # Parse response
            analysis_data = self._parse_json_response(response)

            # Calculate permitting score
            permitting_score = self._calculate_permitting_score(analysis_data)

            # Determine permission status
            permission_str = analysis_data.get("solar_permission", "unknown")
            permission = self._parse_permission(permission_str)

            # Update jurisdiction with findings
            if jurisdiction:
                jurisdiction.solar_permission = permission
                jurisdiction.permitted_zones = analysis_data.get("permitted_zones", [])
                jurisdiction.prohibited_zones = analysis_data.get("prohibited_zones", [])
                jurisdiction.setback_requirements = analysis_data.get("setbacks", {})
                jurisdiction.height_limit_ft = analysis_data.get("height_limit_ft", 0)
                jurisdiction.public_hearing_required = analysis_data.get("public_hearing_required", False)
                jurisdiction.permitting_risk_score = 100 - permitting_score
                jurisdiction.ai_analysis = analysis_data.get("analysis_notes", "")
                jurisdiction.last_analyzed = datetime.now()

            # Determine risks
            risks = analysis_data.get("risks", [])
            if permission == LandUsePermission.PROHIBITED:
                risks.insert(0, "FATAL: Solar development is prohibited in this zoning district")
            elif permission == LandUsePermission.MORATORIUM:
                risks.insert(0, "FATAL: Moratorium on solar development is active")

            return self._build_result(
                success=True,
                data={
                    "solar_permission": permission.value,
                    "permitting_score": permitting_score,
                    "permitted_zones": analysis_data.get("permitted_zones", []),
                    "prohibited_zones": analysis_data.get("prohibited_zones", []),
                    "permits_required": analysis_data.get("permits_required", []),
                    "setbacks": analysis_data.get("setbacks", {}),
                    "height_limit_ft": analysis_data.get("height_limit_ft"),
                    "screening_required": analysis_data.get("screening_required", False),
                    "decommissioning_required": analysis_data.get("decommissioning_required", False),
                    "public_hearing_required": analysis_data.get("public_hearing_required", False),
                    "moratorium_active": analysis_data.get("moratorium_active", False),
                },
                analysis=analysis_data.get("analysis_notes", ""),
                confidence=analysis_data.get("confidence_score", 0.7),
                recommendations=analysis_data.get("recommendations", []),
                risks=risks,
                tokens=tokens,
                start_time=start_time,
            )

        except Exception as e:
            logger.error(f"Permitting analysis failed: {e}")
            return self._build_result(
                success=False,
                error=str(e),
                start_time=start_time,
            )

    def _parse_permission(self, permission_str: str) -> LandUsePermission:
        """Parse permission string to enum."""
        mapping = {
            "by_right": LandUsePermission.BY_RIGHT,
            "conditional_use": LandUsePermission.CONDITIONAL_USE,
            "special_exception": LandUsePermission.SPECIAL_EXCEPTION,
            "variance_required": LandUsePermission.VARIANCE_REQUIRED,
            "prohibited": LandUsePermission.PROHIBITED,
            "moratorium": LandUsePermission.MORATORIUM,
        }
        return mapping.get(permission_str.lower(), LandUsePermission.UNKNOWN)

    def _calculate_permitting_score(self, analysis: dict) -> float:
        """Calculate permitting viability score (0-100)."""
        score = 100.0

        # Permission type impact
        permission = analysis.get("solar_permission", "unknown").lower()
        permission_scores = {
            "by_right": 100,
            "conditional_use": 70,
            "special_exception": 50,
            "variance_required": 30,
            "prohibited": 0,
            "moratorium": 0,
            "unknown": 40,
        }
        score = permission_scores.get(permission, 40)

        # Public hearing penalty
        if analysis.get("public_hearing_required", False):
            score -= 15

        # Moratorium is fatal
        if analysis.get("moratorium_active", False):
            score = 0

        # Risk count penalty
        risks = analysis.get("risks", [])
        score -= min(len(risks) * 5, 25)

        return max(0, min(100, score))

    async def analyze_ordinance_text(
        self,
        ordinance_text: str,
        jurisdiction_name: str,
        state: str,
    ) -> AgentResult:
        """
        Analyze raw ordinance text to extract solar permitting rules.

        This is the core text-to-geography mapping capability.
        """
        start_time = datetime.now()

        system_prompt = """You are an expert at parsing legal zoning ordinances. Extract all solar energy related provisions from the following ordinance text.

For each zoning district mentioned, determine:
1. Whether solar is explicitly permitted, conditionally permitted, or prohibited
2. What type of solar (utility-scale, commercial, residential)
3. Any specific requirements or limitations

Respond in JSON format:
{
    "zones": {
        "zone_code": {
            "name": "Zone Name",
            "solar_utility": "permitted|conditional|prohibited|not_mentioned",
            "solar_commercial": "permitted|conditional|prohibited|not_mentioned",
            "solar_residential": "permitted|conditional|prohibited|not_mentioned",
            "requirements": ["list of requirements"],
            "relevant_sections": ["section references"]
        }
    },
    "general_requirements": {
        "setbacks": {},
        "height_limits": {},
        "lot_coverage": {},
        "screening": "",
        "decommissioning": ""
    },
    "moratorium_info": null or {"active": true, "expiration": "date", "details": ""},
    "key_definitions": {},
    "confidence": 0.0-1.0
}"""

        user_prompt = f"""Analyze this zoning ordinance from {jurisdiction_name}, {state}:

{ordinance_text[:15000]}  # Truncate very long documents

Extract all solar energy related provisions."""

        try:
            response, tokens = await self._call_llm(
                system_prompt,
                user_prompt,
                json_mode=True,
            )

            analysis = self._parse_json_response(response)

            return self._build_result(
                success=True,
                data=analysis,
                analysis=f"Analyzed ordinance for {jurisdiction_name}, {state}",
                confidence=analysis.get("confidence", 0.7),
                tokens=tokens,
                start_time=start_time,
            )

        except Exception as e:
            logger.error(f"Ordinance analysis failed: {e}")
            return self._build_result(
                success=False,
                error=str(e),
                start_time=start_time,
            )

    async def predict_permitting_timeline(
        self,
        jurisdiction: Jurisdiction,
        project_type: str,
        capacity_mw: float,
    ) -> dict:
        """Predict permitting timeline based on jurisdiction and project."""
        # Base timeline by permission type
        base_months = {
            LandUsePermission.BY_RIGHT: 3,
            LandUsePermission.CONDITIONAL_USE: 9,
            LandUsePermission.SPECIAL_EXCEPTION: 12,
            LandUsePermission.VARIANCE_REQUIRED: 18,
        }

        base = base_months.get(jurisdiction.solar_permission, 12)

        # Adjustments
        if jurisdiction.public_hearing_required:
            base += 3

        # Project size factor
        if capacity_mw > 50:
            base += 6
        elif capacity_mw > 20:
            base += 3

        return {
            "estimated_months": base,
            "range_low_months": max(1, base - 3),
            "range_high_months": base + 6,
            "key_milestones": [
                {"name": "Application Submission", "month": 0},
                {"name": "Completeness Review", "month": 1},
                {"name": "Staff Review", "month": base // 2},
                {"name": "Public Hearing", "month": base - 2} if jurisdiction.public_hearing_required else None,
                {"name": "Decision", "month": base},
            ],
            "confidence": 0.7,
        }
