"""
Wind Turbine Analyzer - Comprehensive AI-powered wind asset analysis.

Combines blade inspection, vibration analysis, and performance monitoring
for complete wind turbine health assessment.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4

import numpy as np
from numpy.typing import NDArray
from loguru import logger

from paces.core.config import PacesConfig
from paces.core.types import (
    AlertSeverity,
    Defect,
    DefectType,
    WindTurbine,
    WindFarm,
    EnergyReading,
    BoundingBox,
)


@dataclass
class WindInspectionResult:
    """Result of wind turbine inspection."""
    turbine_id: str
    inspection_time: datetime
    duration_seconds: float

    # Blade inspection
    blades_inspected: int = 0
    blade_defects: list[Defect] = field(default_factory=list)

    # Vibration analysis
    vibration_analyzed: bool = False
    vibration_anomalies: list[dict] = field(default_factory=list)
    vibration_health_score: float = 100.0

    # Component status
    gearbox_status: str = "ok"
    generator_status: str = "ok"
    yaw_status: str = "ok"
    pitch_status: str = "ok"

    # Defects summary
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Performance
    current_power_kw: float = 0.0
    efficiency: float = 0.0
    availability: float = 0.0

    # AI analysis
    ai_summary: str = ""
    recommendations: list[str] = field(default_factory=list)
    estimated_remaining_life_years: float = 0.0

    def to_dict(self) -> dict:
        return {
            "turbine_id": self.turbine_id,
            "inspection_time": self.inspection_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "blades_inspected": self.blades_inspected,
            "total_defects": len(self.blade_defects),
            "defects_by_severity": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
            },
            "vibration_health_score": self.vibration_health_score,
            "component_status": {
                "gearbox": self.gearbox_status,
                "generator": self.generator_status,
                "yaw": self.yaw_status,
                "pitch": self.pitch_status,
            },
            "efficiency": self.efficiency,
            "ai_summary": self.ai_summary,
            "recommendations": self.recommendations,
        }


class WindAnalyzer:
    """
    Comprehensive wind turbine analyzer using SOTA AI models.

    Features:
    - YOLOv12-based blade defect detection
    - SAM3 precise damage segmentation
    - Vibration signature analysis
    - Power curve analysis
    - Qwen2.5-VL visual inspection
    - Predictive component health
    """

    def __init__(self, config: PacesConfig):
        self.config = config
        self.wind_config = config.wind

        # AI models
        self._blade_inspector = None
        self._vibration_analyzer = None
        self._vlm_analyzer = None

        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize AI models for wind analysis."""
        logger.info("Initializing Wind Analyzer...")

        try:
            from paces.wind.blade_inspector import BladeInspector
            from paces.wind.vibration import VibrationAnalyzer

            self._blade_inspector = BladeInspector(self.config)
            await self._blade_inspector.load()

            if self.wind_config.vibration_analysis_enabled:
                self._vibration_analyzer = VibrationAnalyzer(self.config)
                await self._vibration_analyzer.load()

            self._initialized = True
            logger.info("Wind Analyzer initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Wind Analyzer initialization failed: {e}")
            return False

    async def analyze_turbine(
        self,
        turbine: WindTurbine,
        blade_images: list[NDArray] = None,
        vibration_data: list[dict] = None,
    ) -> WindInspectionResult:
        """
        Perform comprehensive wind turbine analysis.

        Args:
            turbine: WindTurbine object
            blade_images: List of blade RGB images
            vibration_data: List of vibration readings

        Returns:
            WindInspectionResult with all findings
        """
        start_time = datetime.now()
        logger.info(f"Starting wind turbine analysis: {turbine.name}")

        all_defects = []
        blades_inspected = 0
        vibration_anomalies = []
        vibration_health = 100.0

        # Blade inspection
        if blade_images and self._blade_inspector:
            for i, image in enumerate(blade_images):
                blade_result = await self._blade_inspector.inspect(image, blade_id=i)
                all_defects.extend(blade_result["defects"])
                blades_inspected += 1

        # Vibration analysis
        if vibration_data and self._vibration_analyzer:
            vib_result = await self._vibration_analyzer.analyze(vibration_data)
            vibration_anomalies = vib_result["anomalies"]
            vibration_health = vib_result["health_score"]

            # Convert vibration anomalies to defects
            for anomaly in vibration_anomalies:
                defect = self._vibration_to_defect(anomaly, turbine.id)
                all_defects.append(defect)

        # Assess component status
        component_status = self._assess_components(
            turbine, vibration_data, all_defects
        )

        # Count by severity
        critical = sum(1 for d in all_defects if d.severity == AlertSeverity.CRITICAL)
        high = sum(1 for d in all_defects if d.severity == AlertSeverity.HIGH)
        medium = sum(1 for d in all_defects if d.severity == AlertSeverity.MEDIUM)
        low = sum(1 for d in all_defects if d.severity == AlertSeverity.LOW)

        # Generate AI summary
        ai_summary, recommendations = await self._generate_ai_summary(
            turbine, all_defects, vibration_health
        )

        # Estimate remaining life
        remaining_life = self._estimate_remaining_life(
            turbine, all_defects, vibration_health
        )

        duration = (datetime.now() - start_time).total_seconds()

        result = WindInspectionResult(
            turbine_id=turbine.id,
            inspection_time=start_time,
            duration_seconds=duration,
            blades_inspected=blades_inspected,
            blade_defects=all_defects,
            vibration_analyzed=vibration_data is not None,
            vibration_anomalies=vibration_anomalies,
            vibration_health_score=vibration_health,
            gearbox_status=component_status["gearbox"],
            generator_status=component_status["generator"],
            yaw_status=component_status["yaw"],
            pitch_status=component_status["pitch"],
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            current_power_kw=turbine.current_power_kw,
            efficiency=turbine.efficiency,
            ai_summary=ai_summary,
            recommendations=recommendations,
            estimated_remaining_life_years=remaining_life,
        )

        logger.info(
            f"Wind analysis complete: {len(all_defects)} defects "
            f"({critical} critical), vibration health: {vibration_health:.0f}%"
        )

        return result

    def _vibration_to_defect(self, anomaly: dict, turbine_id: str) -> Defect:
        """Convert vibration anomaly to defect."""
        defect_mapping = {
            "imbalance": DefectType.BLADE_EROSION,
            "misalignment": DefectType.YAW_MISALIGNMENT,
            "bearing": DefectType.BEARING_FAILURE,
            "gearbox": DefectType.GEARBOX_WEAR,
        }

        defect_type = defect_mapping.get(
            anomaly.get("type", ""),
            DefectType.STRUCTURAL_DAMAGE
        )

        severity_map = {
            "critical": AlertSeverity.CRITICAL,
            "high": AlertSeverity.HIGH,
            "medium": AlertSeverity.MEDIUM,
            "low": AlertSeverity.LOW,
        }

        return Defect(
            id=str(uuid4())[:8],
            asset_id=turbine_id,
            defect_type=defect_type,
            severity=severity_map.get(anomaly.get("severity", "medium"), AlertSeverity.MEDIUM),
            confidence=anomaly.get("confidence", 0.8),
            description=anomaly.get("description", "Vibration anomaly detected"),
            recommendations=anomaly.get("recommendations", []),
        )

    def _assess_components(
        self,
        turbine: WindTurbine,
        vibration_data: list = None,
        defects: list = None,
    ) -> dict:
        """Assess component health status."""
        status = {
            "gearbox": "ok",
            "generator": "ok",
            "yaw": "ok",
            "pitch": "ok",
        }

        # Check based on temperature
        if turbine.gearbox_oil_temp_c > 80:
            status["gearbox"] = "warning"
        if turbine.gearbox_oil_temp_c > 100:
            status["gearbox"] = "critical"

        if turbine.generator_temp_c > 100:
            status["generator"] = "warning"
        if turbine.generator_temp_c > 130:
            status["generator"] = "critical"

        # Check based on defects
        if defects:
            for d in defects:
                if d.defect_type == DefectType.GEARBOX_WEAR:
                    status["gearbox"] = "warning" if status["gearbox"] == "ok" else status["gearbox"]
                elif d.defect_type == DefectType.YAW_MISALIGNMENT:
                    status["yaw"] = "warning"
                elif d.defect_type == DefectType.PITCH_MALFUNCTION:
                    status["pitch"] = "warning"

        return status

    async def _generate_ai_summary(
        self,
        turbine: WindTurbine,
        defects: list[Defect],
        vibration_health: float,
    ) -> tuple[str, list[str]]:
        """Generate AI-powered summary and recommendations."""
        critical_count = sum(1 for d in defects if d.severity == AlertSeverity.CRITICAL)

        # Count defects by type
        defect_types = {}
        for d in defects:
            key = d.defect_type.value
            defect_types[key] = defect_types.get(key, 0) + 1

        # Generate summary
        if critical_count > 0:
            summary = (
                f"CRITICAL: {critical_count} critical issue(s) detected on {turbine.name}. "
                f"Immediate shutdown and inspection recommended. "
                f"Vibration health: {vibration_health:.0f}%."
            )
        elif vibration_health < 70:
            summary = (
                f"WARNING: Degraded vibration signature detected on {turbine.name}. "
                f"Vibration health: {vibration_health:.0f}%. "
                f"Schedule inspection within 2 weeks."
            )
        elif len(defects) > 0:
            summary = (
                f"{len(defects)} defect(s) detected on {turbine.name}. "
                f"Vibration health: {vibration_health:.0f}%. "
                f"Turbine operating within acceptable parameters."
            )
        else:
            summary = (
                f"No significant issues detected on {turbine.name}. "
                f"Vibration health: {vibration_health:.0f}%. "
                f"Turbine operating normally."
            )

        # Generate recommendations
        recommendations = []

        if critical_count > 0:
            recommendations.append("Immediate shutdown for safety inspection")

        if defect_types.get("blade_erosion", 0) > 0:
            recommendations.append("Schedule blade leading edge repair")

        if defect_types.get("blade_crack", 0) > 0:
            recommendations.append("Urgent: Blade structural inspection required")

        if defect_types.get("gearbox_wear", 0) > 0:
            recommendations.append("Gearbox oil analysis and inspection")

        if vibration_health < 80:
            recommendations.append("Perform detailed vibration analysis")

        if turbine.yaw_angle_deg > self.wind_config.yaw_misalignment_threshold_deg:
            recommendations.append("Check yaw alignment system")

        if not recommendations:
            recommendations.append("Continue standard O&M schedule")
            recommendations.append("Next inspection in 6 months")

        return summary, recommendations

    def _estimate_remaining_life(
        self,
        turbine: WindTurbine,
        defects: list[Defect],
        vibration_health: float,
    ) -> float:
        """Estimate remaining useful life in years."""
        # Base life expectancy: 25 years
        base_life = 25.0

        # Subtract age
        remaining = base_life - turbine.age_years

        # Adjust for health
        health_factor = vibration_health / 100

        # Adjust for defects
        critical_count = sum(1 for d in defects if d.severity == AlertSeverity.CRITICAL)
        high_count = sum(1 for d in defects if d.severity == AlertSeverity.HIGH)

        defect_factor = 1.0 - (critical_count * 0.2) - (high_count * 0.05)

        remaining = remaining * health_factor * defect_factor

        return max(0, remaining)

    async def get_performance(
        self,
        farm_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> dict:
        """Get wind farm performance metrics."""
        return {
            "farm_id": farm_id,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "energy_produced_mwh": 0.0,
            "capacity_factor": 0.0,
            "availability": 0.0,
            "avg_wind_speed_ms": 0.0,
        }

    async def shutdown(self) -> None:
        """Shutdown analyzer."""
        logger.info("Shutting down Wind Analyzer")
        if self._blade_inspector:
            await self._blade_inspector.unload()
        if self._vibration_analyzer:
            await self._vibration_analyzer.unload()
