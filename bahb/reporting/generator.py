"""Inspection report generation for BAHB system."""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from numpy.typing import NDArray
from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger

from bahb.core.types import (
    Anomaly,
    Detection,
    InspectionResult,
    InspectionSession,
    SeverityLevel,
    ThermalReading,
)


class ReportGenerator:
    """
    Generate comprehensive inspection reports in multiple formats.

    Supported formats:
    - PDF: Professional printable reports
    - HTML: Interactive web-based reports
    - JSON: Machine-readable data export
    - Markdown: Documentation-friendly format
    """

    def __init__(
        self,
        template_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ):
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self.output_dir = output_dir or Path("/data/bahb/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self._env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Register custom filters
        self._env.filters["severity_color"] = self._severity_color
        self._env.filters["format_temp"] = self._format_temp
        self._env.filters["format_datetime"] = self._format_datetime

    def generate(
        self,
        session: InspectionSession,
        results: list[InspectionResult],
        format: str = "pdf",
        include_images: bool = True,
        include_thermal: bool = True,
    ) -> Path:
        """
        Generate inspection report.

        Args:
            session: Inspection session metadata
            results: List of inspection results
            format: Output format (pdf, html, json, markdown)
            include_images: Include annotated images
            include_thermal: Include thermal analysis images

        Returns:
            Path to generated report
        """
        logger.info(f"Generating {format.upper()} report for session {session.session_id}")

        # Prepare report data
        report_data = self._prepare_report_data(session, results)

        # Generate based on format
        if format == "pdf":
            return self._generate_pdf(report_data, session.session_id, include_images)
        elif format == "html":
            return self._generate_html(report_data, session.session_id, include_images)
        elif format == "json":
            return self._generate_json(report_data, session.session_id)
        elif format == "markdown":
            return self._generate_markdown(report_data, session.session_id)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _prepare_report_data(
        self,
        session: InspectionSession,
        results: list[InspectionResult],
    ) -> dict:
        """Prepare comprehensive report data."""
        # Aggregate anomalies
        all_anomalies = []
        all_detections = []

        for result in results:
            all_anomalies.extend(result.anomalies)
            all_detections.extend(result.detections)

        # Categorize anomalies by severity
        severity_counts = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 0,
            SeverityLevel.MEDIUM: 0,
            SeverityLevel.LOW: 0,
            SeverityLevel.INFO: 0,
        }

        for anomaly in all_anomalies:
            severity_counts[anomaly.severity] += 1

        # Group anomalies by type
        anomalies_by_type: dict[str, list[Anomaly]] = {}
        for anomaly in all_anomalies:
            if anomaly.type not in anomalies_by_type:
                anomalies_by_type[anomaly.type] = []
            anomalies_by_type[anomaly.type].append(anomaly)

        # Detection statistics
        detection_counts: dict[str, int] = {}
        for det in all_detections:
            if det.class_name not in detection_counts:
                detection_counts[det.class_name] = 0
            detection_counts[det.class_name] += 1

        # Thermal summary
        thermal_data = []
        for result in results:
            if result.thermal_reading:
                thermal_data.append({
                    "frame_id": result.frame_id,
                    "min_temp": result.thermal_reading.min_temp,
                    "max_temp": result.thermal_reading.max_temp,
                    "mean_temp": result.thermal_reading.mean_temp,
                    "hotspot_count": len(result.thermal_reading.hotspot_locations),
                })

        thermal_summary = {}
        if thermal_data:
            thermal_summary = {
                "overall_min": min(t["min_temp"] for t in thermal_data),
                "overall_max": max(t["max_temp"] for t in thermal_data),
                "overall_mean": sum(t["mean_temp"] for t in thermal_data) / len(thermal_data),
                "total_hotspots": sum(t["hotspot_count"] for t in thermal_data),
            }

        # VLM insights
        vlm_insights = []
        for result in results:
            if result.vlm_description:
                vlm_insights.append({
                    "frame_id": result.frame_id,
                    "description": result.vlm_description,
                    "recommendations": result.vlm_recommendations or [],
                })

        return {
            "session": session.to_dict(),
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_frames": len(results),
                "total_detections": len(all_detections),
                "total_anomalies": len(all_anomalies),
                "severity_counts": {k.name: v for k, v in severity_counts.items()},
            },
            "anomalies": [a.to_dict() for a in all_anomalies],
            "anomalies_by_type": {k: [a.to_dict() for a in v] for k, v in anomalies_by_type.items()},
            "detection_counts": detection_counts,
            "thermal_summary": thermal_summary,
            "thermal_data": thermal_data,
            "vlm_insights": vlm_insights,
            "recommendations": self._generate_recommendations(all_anomalies, thermal_summary),
        }

    def _generate_recommendations(
        self,
        anomalies: list[Anomaly],
        thermal_summary: dict,
    ) -> list[dict]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Critical anomalies
        critical = [a for a in anomalies if a.severity == SeverityLevel.CRITICAL]
        if critical:
            recommendations.append({
                "priority": "IMMEDIATE",
                "title": "Critical Issues Require Immediate Attention",
                "description": f"{len(critical)} critical anomaly(s) detected. "
                              "Immediate inspection and possible shutdown required.",
                "items": [a.description for a in critical[:5]],
            })

        # High severity
        high = [a for a in anomalies if a.severity == SeverityLevel.HIGH]
        if high:
            recommendations.append({
                "priority": "HIGH",
                "title": "High Priority Maintenance Required",
                "description": f"{len(high)} high-severity issue(s) detected. "
                              "Schedule maintenance within 24-48 hours.",
                "items": list(set([rec for a in high for rec in a.recommendations]))[:5],
            })

        # Thermal recommendations
        if thermal_summary and thermal_summary.get("overall_max", 0) > 80:
            recommendations.append({
                "priority": "HIGH",
                "title": "Thermal Anomalies Detected",
                "description": f"Maximum temperature of {thermal_summary['overall_max']:.1f}°C recorded. "
                              f"{thermal_summary.get('total_hotspots', 0)} hotspots identified.",
                "items": [
                    "Verify thermal readings with calibrated equipment",
                    "Check for loose connections or overloaded circuits",
                    "Inspect cooling systems if applicable",
                ],
            })

        # Medium severity
        medium = [a for a in anomalies if a.severity == SeverityLevel.MEDIUM]
        if medium:
            recommendations.append({
                "priority": "MEDIUM",
                "title": "Scheduled Maintenance Recommended",
                "description": f"{len(medium)} medium-severity issue(s) detected. "
                              "Include in next scheduled maintenance window.",
                "items": list(set([rec for a in medium for rec in a.recommendations]))[:5],
            })

        # General recommendations
        if not recommendations:
            recommendations.append({
                "priority": "INFO",
                "title": "No Significant Issues Detected",
                "description": "Equipment appears to be operating within normal parameters.",
                "items": [
                    "Continue routine inspection schedule",
                    "Archive this report for trend analysis",
                ],
            })

        return recommendations

    def _generate_pdf(
        self,
        report_data: dict,
        session_id: str,
        include_images: bool,
    ) -> Path:
        """Generate PDF report."""
        try:
            from weasyprint import HTML

            # First generate HTML
            html_content = self._render_html_template(report_data, include_images)

            # Convert to PDF
            output_path = self.output_dir / f"{session_id}_report.pdf"
            HTML(string=html_content).write_pdf(str(output_path))

            logger.info(f"PDF report generated: {output_path}")
            return output_path

        except ImportError:
            logger.warning("WeasyPrint not available, falling back to HTML")
            return self._generate_html(report_data, session_id, include_images)

    def _generate_html(
        self,
        report_data: dict,
        session_id: str,
        include_images: bool,
    ) -> Path:
        """Generate HTML report."""
        html_content = self._render_html_template(report_data, include_images)

        output_path = self.output_dir / f"{session_id}_report.html"
        with open(output_path, "w") as f:
            f.write(html_content)

        logger.info(f"HTML report generated: {output_path}")
        return output_path

    def _render_html_template(self, report_data: dict, include_images: bool) -> str:
        """Render HTML template with report data."""
        try:
            template = self._env.get_template("inspection_report.html")
            return template.render(**report_data, include_images=include_images)
        except Exception as e:
            logger.warning(f"Template not found, using built-in template: {e}")
            return self._render_builtin_html(report_data, include_images)

    def _render_builtin_html(self, report_data: dict, include_images: bool) -> str:
        """Render built-in HTML template."""
        session = report_data["session"]
        summary = report_data["summary"]
        recommendations = report_data["recommendations"]

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Inspection Report - {session.get('session_id', 'Unknown')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a237e; border-bottom: 3px solid #1a237e; padding-bottom: 10px; }}
        h2 {{ color: #303f9f; margin-top: 30px; }}
        h3 {{ color: #5c6bc0; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: #e8eaf6; padding: 20px; border-radius: 8px; text-align: center; }}
        .summary-card .value {{ font-size: 2em; font-weight: bold; color: #1a237e; }}
        .severity-critical {{ background: #ffebee; border-left: 4px solid #c62828; }}
        .severity-high {{ background: #fff3e0; border-left: 4px solid #ef6c00; }}
        .severity-medium {{ background: #fff8e1; border-left: 4px solid #fbc02d; }}
        .severity-low {{ background: #e8f5e9; border-left: 4px solid #43a047; }}
        .severity-info {{ background: #e3f2fd; border-left: 4px solid #1976d2; }}
        .anomaly-card {{ padding: 15px; margin: 10px 0; border-radius: 4px; }}
        .recommendation {{ padding: 20px; margin: 15px 0; border-radius: 8px; }}
        .priority-immediate {{ background: #ffcdd2; }}
        .priority-high {{ background: #ffe0b2; }}
        .priority-medium {{ background: #fff9c4; }}
        .priority-info {{ background: #bbdefb; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #e8eaf6; color: #1a237e; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛸 Infrastructure Inspection Report</h1>

        <div class="meta">
            <p><strong>Session ID:</strong> {session.get('session_id', 'N/A')}</p>
            <p><strong>Site:</strong> {session.get('site_name', 'Unknown')}</p>
            <p><strong>Inspection Type:</strong> {session.get('inspection_type', 'General')}</p>
            <p><strong>Date:</strong> {session.get('start_time', 'N/A')}</p>
            <p><strong>Generated:</strong> {report_data.get('generated_at', 'N/A')}</p>
        </div>

        <h2>Executive Summary</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="value">{summary.get('total_frames', 0)}</div>
                <div class="label">Frames Analyzed</div>
            </div>
            <div class="summary-card">
                <div class="value">{summary.get('total_detections', 0)}</div>
                <div class="label">Objects Detected</div>
            </div>
            <div class="summary-card">
                <div class="value">{summary.get('total_anomalies', 0)}</div>
                <div class="label">Anomalies Found</div>
            </div>
            <div class="summary-card">
                <div class="value" style="color: {'#c62828' if summary.get('severity_counts', {}).get('CRITICAL', 0) > 0 else '#43a047'}">
                    {summary.get('severity_counts', {}).get('CRITICAL', 0)}
                </div>
                <div class="label">Critical Issues</div>
            </div>
        </div>

        <h2>Severity Breakdown</h2>
        <table>
            <tr>
                <th>Severity</th>
                <th>Count</th>
                <th>Status</th>
            </tr>
            <tr class="severity-critical">
                <td>Critical</td>
                <td>{summary.get('severity_counts', {}).get('CRITICAL', 0)}</td>
                <td>Immediate action required</td>
            </tr>
            <tr class="severity-high">
                <td>High</td>
                <td>{summary.get('severity_counts', {}).get('HIGH', 0)}</td>
                <td>Schedule within 24-48 hours</td>
            </tr>
            <tr class="severity-medium">
                <td>Medium</td>
                <td>{summary.get('severity_counts', {}).get('MEDIUM', 0)}</td>
                <td>Include in next maintenance</td>
            </tr>
            <tr class="severity-low">
                <td>Low</td>
                <td>{summary.get('severity_counts', {}).get('LOW', 0)}</td>
                <td>Monitor and document</td>
            </tr>
            <tr class="severity-info">
                <td>Info</td>
                <td>{summary.get('severity_counts', {}).get('INFO', 0)}</td>
                <td>For reference</td>
            </tr>
        </table>

        <h2>Recommendations</h2>
        {''.join([self._render_recommendation(r) for r in recommendations])}

        <h2>Anomalies Detail</h2>
        {''.join([self._render_anomaly(a) for a in report_data.get('anomalies', [])[:20]])}

        <h2>Thermal Analysis</h2>
        {self._render_thermal_summary(report_data.get('thermal_summary', {}))}

        <h2>Detection Summary</h2>
        {self._render_detection_table(report_data.get('detection_counts', {}))}

        <div class="footer">
            <p>Generated by BAHB Drone Inspection System</p>
            <p>This report is automatically generated and should be verified by qualified personnel.</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _render_recommendation(self, rec: dict) -> str:
        """Render a recommendation block."""
        priority_class = f"priority-{rec.get('priority', 'info').lower()}"
        items_html = "".join([f"<li>{item}</li>" for item in rec.get('items', [])])

        return f"""
        <div class="recommendation {priority_class}">
            <h3>{rec.get('priority', 'INFO')}: {rec.get('title', 'Recommendation')}</h3>
            <p>{rec.get('description', '')}</p>
            <ul>{items_html}</ul>
        </div>
        """

    def _render_anomaly(self, anomaly: dict) -> str:
        """Render an anomaly card."""
        severity = anomaly.get('severity', 'INFO').lower()
        return f"""
        <div class="anomaly-card severity-{severity}">
            <h3>{anomaly.get('type', 'Unknown')} [{anomaly.get('severity', 'INFO')}]</h3>
            <p>{anomaly.get('description', '')}</p>
            <p><small>Location: {anomaly.get('location', 'N/A')} | Time: {anomaly.get('timestamp', 'N/A')}</small></p>
        </div>
        """

    def _render_thermal_summary(self, thermal: dict) -> str:
        """Render thermal summary."""
        if not thermal:
            return "<p>No thermal data available.</p>"

        return f"""
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Minimum Temperature</td><td>{thermal.get('overall_min', 0):.1f}°C</td></tr>
            <tr><td>Maximum Temperature</td><td>{thermal.get('overall_max', 0):.1f}°C</td></tr>
            <tr><td>Average Temperature</td><td>{thermal.get('overall_mean', 0):.1f}°C</td></tr>
            <tr><td>Total Hotspots</td><td>{thermal.get('total_hotspots', 0)}</td></tr>
        </table>
        """

    def _render_detection_table(self, counts: dict) -> str:
        """Render detection counts table."""
        if not counts:
            return "<p>No detections recorded.</p>"

        rows = "".join([
            f"<tr><td>{name}</td><td>{count}</td></tr>"
            for name, count in sorted(counts.items(), key=lambda x: -x[1])[:15]
        ])

        return f"""
        <table>
            <tr><th>Object Type</th><th>Count</th></tr>
            {rows}
        </table>
        """

    def _generate_json(self, report_data: dict, session_id: str) -> Path:
        """Generate JSON report."""
        output_path = self.output_dir / f"{session_id}_report.json"

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"JSON report generated: {output_path}")
        return output_path

    def _generate_markdown(self, report_data: dict, session_id: str) -> Path:
        """Generate Markdown report."""
        session = report_data["session"]
        summary = report_data["summary"]

        md = f"""# Infrastructure Inspection Report

## Session Information
- **Session ID:** {session.get('session_id', 'N/A')}
- **Site:** {session.get('site_name', 'Unknown')}
- **Type:** {session.get('inspection_type', 'General')}
- **Date:** {session.get('start_time', 'N/A')}

## Summary
| Metric | Value |
|--------|-------|
| Frames Analyzed | {summary.get('total_frames', 0)} |
| Objects Detected | {summary.get('total_detections', 0)} |
| Anomalies Found | {summary.get('total_anomalies', 0)} |
| Critical Issues | {summary.get('severity_counts', {}).get('CRITICAL', 0)} |

## Recommendations
"""
        for rec in report_data.get("recommendations", []):
            md += f"\n### {rec.get('priority', 'INFO')}: {rec.get('title', '')}\n"
            md += f"{rec.get('description', '')}\n\n"
            for item in rec.get("items", []):
                md += f"- {item}\n"

        md += "\n## Anomalies\n"
        for anomaly in report_data.get("anomalies", [])[:20]:
            md += f"\n### {anomaly.get('type', 'Unknown')} [{anomaly.get('severity', 'INFO')}]\n"
            md += f"{anomaly.get('description', '')}\n"

        output_path = self.output_dir / f"{session_id}_report.md"
        with open(output_path, "w") as f:
            f.write(md)

        logger.info(f"Markdown report generated: {output_path}")
        return output_path

    @staticmethod
    def _severity_color(severity: str) -> str:
        """Jinja filter for severity colors."""
        colors = {
            "CRITICAL": "#c62828",
            "HIGH": "#ef6c00",
            "MEDIUM": "#fbc02d",
            "LOW": "#43a047",
            "INFO": "#1976d2",
        }
        return colors.get(severity, "#666666")

    @staticmethod
    def _format_temp(temp: float) -> str:
        """Jinja filter for temperature formatting."""
        return f"{temp:.1f}°C"

    @staticmethod
    def _format_datetime(dt: str) -> str:
        """Jinja filter for datetime formatting."""
        try:
            parsed = datetime.fromisoformat(dt)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return dt

    def add_image_to_report(
        self,
        image: NDArray,
        caption: str = "",
    ) -> str:
        """Convert image to base64 for embedding in HTML reports."""
        _, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        b64 = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"
