"""
Report Agent - Automated feasibility report generation.

Generates comprehensive PDF and HTML reports for site assessments.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from loguru import logger

from paces.agents.base import BaseAgent, AgentResult
from paces.core.types import (
    Parcel,
    SiteScore,
    FeasibilityReport,
    GridConnection,
    EnvironmentalScreening,
    Jurisdiction,
)


class ReportAgent(BaseAgent):
    """
    Report generation agent.

    Generates:
    - Executive summary reports
    - Detailed feasibility reports
    - Site comparison reports
    - Pipeline status reports
    """

    def __init__(self):
        super().__init__(
            name="ReportAgent",
            model="claude-3-5-sonnet-20241022",
        )

    async def execute(
        self,
        feasibility: FeasibilityReport,
        output_format: str = "markdown",
    ) -> AgentResult:
        """
        Generate feasibility report.

        Args:
            feasibility: FeasibilityReport with all analysis data
            output_format: Output format (markdown, html, pdf)

        Returns:
            AgentResult with generated report
        """
        start_time = datetime.now()

        try:
            if output_format == "markdown":
                report = self._generate_markdown_report(feasibility)
            elif output_format == "html":
                report = self._generate_html_report(feasibility)
            else:
                report = self._generate_markdown_report(feasibility)

            return self._build_result(
                success=True,
                data={
                    "report": report,
                    "format": output_format,
                    "parcel_id": feasibility.parcel_id,
                },
                analysis=f"Generated {output_format} report for parcel {feasibility.parcel_id}",
                confidence=1.0,
                start_time=start_time,
            )

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return self._build_result(
                success=False,
                error=str(e),
                start_time=start_time,
            )

    def _generate_markdown_report(self, report: FeasibilityReport) -> str:
        """Generate markdown feasibility report."""
        parcel = report.parcel
        score = report.site_score

        md = f"""# Solar Site Feasibility Report

**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M')}
**Report ID:** {report.id}

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Viability** | {report.overall_viability.upper()} |
| **Site Score** | {score.overall_score:.0f}/100 |
| **Recommendation** | {report.proceed_recommendation.upper()} |
| **Recommended Capacity** | {report.recommended_capacity_mw:.1f} MW DC |
| **Estimated CAPEX** | ${report.estimated_capex:,.0f} |
| **Estimated LCOE** | ${report.estimated_lcoe:.2f}/MWh |

---

## Site Information

### Location
- **Address:** {parcel.address or 'N/A'}
- **APN:** {parcel.apn}
- **Municipality:** {parcel.municipality}
- **County:** {parcel.county}
- **State:** {parcel.state}

### Land Characteristics
- **Total Acreage:** {parcel.acreage:.2f} acres
- **Usable Acreage:** {parcel.usable_acreage or parcel.acreage:.2f} acres
- **Current Use:** {parcel.land_use_current}
- **Zoning:** {parcel.zoning_code} ({parcel.zoning_type.value})
- **Average Slope:** {parcel.avg_slope_pct:.1f}%

### Ownership
- **Owner:** {parcel.owner_name}
- **Owner Type:** {parcel.owner_type}

---

## Analysis Scores

| Category | Score | Weight | Weighted |
|----------|-------|--------|----------|
| Permitting | {score.permitting_score:.0f}/100 | 30% | {score.permitting_score * 0.3:.0f} |
| Grid | {score.grid_score:.0f}/100 | 30% | {score.grid_score * 0.3:.0f} |
| Environmental | {score.environmental_score:.0f}/100 | 20% | {score.environmental_score * 0.2:.0f} |
| Land | {score.land_score:.0f}/100 | 20% | {score.land_score * 0.2:.0f} |
| **Overall** | **{score.overall_score:.0f}/100** | **100%** | **{score.overall_score:.0f}** |

---

## Permitting Analysis

**Solar Permission Status:** {score.permitting_factors.get('permission_type', 'Unknown')}
**Public Hearing Required:** {'Yes' if score.permitting_factors.get('public_hearing') else 'No'}

---

## Grid Interconnection

**Distance to Substation:** {score.grid_factors.get('distance_miles', 0):.1f} miles
**Estimated Cost:** ${score.grid_factors.get('cost_per_mw', 0):,.0f}/MW

---

## Environmental Screening

**Risk Level:** {score.environmental_factors.get('risk_level', 'Unknown')}
**Constraints Found:** {len(score.environmental_factors.get('constraints', []))}

---

## Key Risks

"""
        if score.fatal_flaws:
            md += "### Fatal Flaws\n"
            for flaw in score.fatal_flaws:
                md += f"- :x: {flaw}\n"
            md += "\n"

        if report.key_risks:
            md += "### Other Risks\n"
            for risk in report.key_risks:
                md += f"- :warning: {risk}\n"

        md += f"""
---

## Next Steps

"""
        for i, step in enumerate(report.next_steps, 1):
            md += f"{i}. {step}\n"

        md += f"""
---

## Financial Summary

| Metric | Value |
|--------|-------|
| Recommended Capacity | {report.recommended_capacity_mw:.1f} MW DC |
| Estimated CAPEX | ${report.estimated_capex:,.0f} |
| CAPEX per Watt | ${report.estimated_capex / (report.recommended_capacity_mw * 1_000_000):.2f}/W |
| Estimated LCOE | ${report.estimated_lcoe:.2f}/MWh |
| Development Timeline | {report.estimated_timeline_months} months |

---

*This report is for informational purposes only and should not be relied upon as the sole basis for investment decisions. Additional due diligence is recommended.*

**Generated by Paces AI**
"""
        return md

    def _generate_html_report(self, report: FeasibilityReport) -> str:
        """Generate HTML feasibility report."""
        # Convert markdown to HTML (simplified)
        md = self._generate_markdown_report(report)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Site Feasibility Report - {report.parcel_id}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
        h2 {{ color: #34a853; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
        .score-excellent {{ color: #34a853; font-weight: bold; }}
        .score-good {{ color: #1a73e8; }}
        .score-fair {{ color: #fbbc04; }}
        .score-poor {{ color: #ea4335; }}
        .risk {{ color: #ea4335; }}
        .warning {{ color: #fbbc04; }}
    </style>
</head>
<body>
    <pre>{md}</pre>
</body>
</html>"""
        return html

    async def generate_comparison_report(
        self,
        parcels: list[Parcel],
        scores: list[SiteScore],
    ) -> str:
        """Generate site comparison report."""
        md = """# Site Comparison Report

| Rank | Parcel | Location | Acreage | Overall | Permitting | Grid | Environmental | Recommendation |
|------|--------|----------|---------|---------|------------|------|---------------|----------------|
"""
        # Sort by overall score
        paired = list(zip(parcels, scores))
        paired.sort(key=lambda x: x[1].overall_score, reverse=True)

        for rank, (parcel, score) in enumerate(paired, 1):
            md += f"| {rank} | {parcel.apn} | {parcel.county}, {parcel.state} | {parcel.acreage:.0f} | "
            md += f"{score.overall_score:.0f} | {score.permitting_score:.0f} | {score.grid_score:.0f} | "
            md += f"{score.environmental_score:.0f} | {score.proceed_recommendation} |\n"

        return md
