"""Thermal image analysis for infrastructure inspection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np
from numpy.typing import NDArray
from scipy import ndimage
from loguru import logger

from bahb.core.config import ThermalAnalysisConfig
from bahb.core.types import BoundingBox, ThermalReading


@dataclass
class ThermalZone:
    """Temperature zone for specific equipment type."""
    name: str
    normal_range: tuple[float, float]
    warning_range: tuple[float, float]
    critical_range: tuple[float, float]

    def get_status(self, temperature: float) -> str:
        """Get status based on temperature."""
        if self.normal_range[0] <= temperature <= self.normal_range[1]:
            return "normal"
        elif self.warning_range[0] <= temperature <= self.warning_range[1]:
            return "warning"
        elif self.critical_range[0] <= temperature <= self.critical_range[1]:
            return "critical"
        elif temperature > self.critical_range[1]:
            return "critical"
        else:
            return "unknown"


class ThermalAnalyzer:
    """
    Advanced thermal image analysis for infrastructure inspection.

    Features:
    - Hot spot detection with clustering
    - Temperature differential analysis
    - Equipment-specific thermal zones
    - Trend analysis over time
    - Radiometric calibration
    """

    # Default temperature zones for common equipment
    DEFAULT_ZONES = {
        "transformer": ThermalZone(
            "transformer",
            normal_range=(20, 65),
            warning_range=(65, 85),
            critical_range=(85, 150),
        ),
        "conductor": ThermalZone(
            "conductor",
            normal_range=(15, 50),
            warning_range=(50, 75),
            critical_range=(75, 120),
        ),
        "switchgear": ThermalZone(
            "switchgear",
            normal_range=(20, 55),
            warning_range=(55, 75),
            critical_range=(75, 110),
        ),
        "insulator": ThermalZone(
            "insulator",
            normal_range=(15, 45),
            warning_range=(45, 65),
            critical_range=(65, 100),
        ),
        "server": ThermalZone(
            "server",
            normal_range=(25, 45),
            warning_range=(45, 60),
            critical_range=(60, 85),
        ),
        "hvac": ThermalZone(
            "hvac",
            normal_range=(10, 40),
            warning_range=(40, 55),
            critical_range=(55, 80),
        ),
    }

    def __init__(self, config: ThermalAnalysisConfig):
        self.config = config
        self.baseline_temp = config.baseline_temp
        self.hotspot_threshold = config.hotspot_threshold
        self.critical_threshold = config.critical_threshold
        self.cold_spot_threshold = config.cold_spot_threshold

        # Build zones from config
        self.zones = self.DEFAULT_ZONES.copy()
        for name, zone_config in config.zones.items():
            self.zones[name] = ThermalZone(
                name=name,
                normal_range=tuple(zone_config.normal_range),
                warning_range=tuple(zone_config.warning_range),
                critical_range=tuple(zone_config.critical_range),
            )

        # Temperature history for trend analysis
        self._temp_history: dict[str, list[float]] = {}
        self._max_history = 100

    def analyze(
        self,
        thermal_image: NDArray,
        reference_temp: Optional[float] = None,
        region_of_interest: Optional[BoundingBox] = None,
    ) -> ThermalReading:
        """
        Perform comprehensive thermal analysis.

        Args:
            thermal_image: Raw thermal data (float32 temperatures) or colorized image
            reference_temp: Reference/ambient temperature
            region_of_interest: Optional ROI to focus analysis

        Returns:
            ThermalReading with analysis results
        """
        # Convert colorized image to temperatures if needed
        if thermal_image.dtype == np.uint8:
            temp_map = self._estimate_temperatures_from_colorized(thermal_image)
        else:
            temp_map = thermal_image.astype(np.float32)

        # Apply ROI if specified
        if region_of_interest:
            x1, y1 = int(region_of_interest.x1), int(region_of_interest.y1)
            x2, y2 = int(region_of_interest.x2), int(region_of_interest.y2)
            temp_map = temp_map[y1:y2, x1:x2]

        # Calculate statistics
        min_temp = float(np.min(temp_map))
        max_temp = float(np.max(temp_map))
        mean_temp = float(np.mean(temp_map))

        # Set reference
        ref_temp = reference_temp or self.baseline_temp

        # Find hotspots
        hotspot_threshold = ref_temp + self.hotspot_threshold
        hotspot_mask = temp_map > hotspot_threshold
        hotspot_locations = self._find_local_maxima(temp_map, hotspot_mask)

        # Find coldspots
        coldspot_threshold = ref_temp + self.cold_spot_threshold
        coldspot_mask = temp_map < coldspot_threshold
        coldspot_locations = self._find_local_minima(temp_map, coldspot_mask)

        return ThermalReading(
            min_temp=min_temp,
            max_temp=max_temp,
            mean_temp=mean_temp,
            hotspot_locations=hotspot_locations,
            coldspot_locations=coldspot_locations,
            temperature_map=temp_map,
        )

    def _estimate_temperatures_from_colorized(
        self,
        colorized: NDArray,
        temp_range: tuple[float, float] = (-20, 120),
    ) -> NDArray[np.float32]:
        """
        Estimate temperatures from a colorized thermal image.

        This is an approximation - actual temperatures require
        radiometric data from the thermal sensor.
        """
        # Convert to grayscale based on "heat" intensity
        if len(colorized.shape) == 3:
            # For ironbow/rainbow palettes, red channel often correlates with heat
            b, g, r = cv2.split(colorized)

            # Weighted combination
            intensity = (0.5 * r + 0.3 * g + 0.2 * (255 - b)).astype(np.float32)
            intensity = intensity / 255.0
        else:
            intensity = colorized.astype(np.float32) / 255.0

        # Map to temperature range
        temp_min, temp_max = temp_range
        temperatures = intensity * (temp_max - temp_min) + temp_min

        return temperatures

    def _find_local_maxima(
        self,
        temp_map: NDArray,
        mask: NDArray,
        min_distance: int = 20,
        threshold_percentile: float = 95,
    ) -> list[tuple[int, int]]:
        """Find local temperature maxima (hotspots)."""
        if not np.any(mask):
            return []

        # Apply mask
        masked = np.where(mask, temp_map, -np.inf)

        # Find local maxima using dilation
        dilated = ndimage.maximum_filter(masked, size=min_distance)
        local_max = (masked == dilated) & mask

        # Get coordinates
        coords = np.argwhere(local_max)

        # Filter by percentile threshold
        if len(coords) > 0:
            threshold = np.percentile(temp_map[mask], threshold_percentile)
            filtered = [
                (int(c[1]), int(c[0]))  # x, y format
                for c in coords
                if temp_map[c[0], c[1]] >= threshold
            ]
            return filtered[:20]  # Limit to top 20

        return []

    def _find_local_minima(
        self,
        temp_map: NDArray,
        mask: NDArray,
        min_distance: int = 20,
    ) -> list[tuple[int, int]]:
        """Find local temperature minima (coldspots)."""
        if not np.any(mask):
            return []

        masked = np.where(mask, temp_map, np.inf)
        dilated = ndimage.minimum_filter(masked, size=min_distance)
        local_min = (masked == dilated) & mask

        coords = np.argwhere(local_min)

        if len(coords) > 0:
            filtered = [
                (int(c[1]), int(c[0]))
                for c in coords
            ]
            return filtered[:10]

        return []

    def analyze_region(
        self,
        temp_map: NDArray,
        bbox: BoundingBox,
        equipment_type: Optional[str] = None,
    ) -> dict:
        """
        Analyze thermal characteristics of a specific region.

        Args:
            temp_map: Full temperature map
            bbox: Bounding box of region
            equipment_type: Type of equipment for zone-based analysis

        Returns:
            Dictionary with regional analysis
        """
        x1, y1 = int(max(0, bbox.x1)), int(max(0, bbox.y1))
        x2, y2 = int(min(temp_map.shape[1], bbox.x2)), int(min(temp_map.shape[0], bbox.y2))

        if x2 <= x1 or y2 <= y1:
            return {"error": "Invalid region"}

        region = temp_map[y1:y2, x1:x2]

        analysis = {
            "min_temp": float(np.min(region)),
            "max_temp": float(np.max(region)),
            "mean_temp": float(np.mean(region)),
            "std_temp": float(np.std(region)),
            "delta_t": float(np.max(region) - np.min(region)),
        }

        # Zone-based status
        if equipment_type and equipment_type in self.zones:
            zone = self.zones[equipment_type]
            analysis["status"] = zone.get_status(analysis["max_temp"])
            analysis["zone"] = equipment_type

        # Gradient analysis
        gradient_x = np.gradient(region, axis=1)
        gradient_y = np.gradient(region, axis=0)
        gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)

        analysis["max_gradient"] = float(np.max(gradient_magnitude))
        analysis["mean_gradient"] = float(np.mean(gradient_magnitude))

        return analysis

    def compare_regions(
        self,
        temp_map: NDArray,
        region1: BoundingBox,
        region2: BoundingBox,
    ) -> dict:
        """
        Compare thermal signatures of two regions.

        Useful for comparing similar equipment (e.g., phases in 3-phase system).
        """
        r1 = self.analyze_region(temp_map, region1)
        r2 = self.analyze_region(temp_map, region2)

        comparison = {
            "region1": r1,
            "region2": r2,
            "mean_diff": abs(r1["mean_temp"] - r2["mean_temp"]),
            "max_diff": abs(r1["max_temp"] - r2["max_temp"]),
        }

        # Flag significant differences
        if comparison["mean_diff"] > 10:
            comparison["significant_difference"] = True
            comparison["analysis"] = "Significant temperature difference detected between regions"
        else:
            comparison["significant_difference"] = False

        return comparison

    def detect_anomalies_advanced(
        self,
        temp_map: NDArray,
        detections: list,
    ) -> list[dict]:
        """
        Advanced anomaly detection combining thermal and detection data.

        Analyzes each detection for thermal anomalies specific to equipment type.
        """
        anomalies = []

        for det in detections:
            bbox = det.bbox
            equipment_type = self._map_class_to_equipment(det.class_name)

            region_analysis = self.analyze_region(temp_map, bbox, equipment_type)

            if "error" in region_analysis:
                continue

            # Check for anomalies
            is_anomaly = False
            severity = "normal"
            reason = ""

            if region_analysis.get("status") == "critical":
                is_anomaly = True
                severity = "critical"
                reason = f"Temperature {region_analysis['max_temp']:.1f}°C exceeds critical threshold"

            elif region_analysis.get("status") == "warning":
                is_anomaly = True
                severity = "warning"
                reason = f"Temperature {region_analysis['max_temp']:.1f}°C in warning range"

            # High temperature gradient can indicate problems
            if region_analysis["max_gradient"] > 5.0:  # °C per pixel
                is_anomaly = True
                if severity == "normal":
                    severity = "warning"
                reason += f" High thermal gradient detected ({region_analysis['max_gradient']:.1f}°C/px)"

            if is_anomaly:
                anomalies.append({
                    "detection": det,
                    "thermal_analysis": region_analysis,
                    "severity": severity,
                    "reason": reason.strip(),
                })

        return anomalies

    def _map_class_to_equipment(self, class_name: str) -> str:
        """Map detection class to equipment type for zone lookup."""
        mapping = {
            "transformer": "transformer",
            "insulator": "insulator",
            "conductor": "conductor",
            "switchgear": "switchgear",
            "circuit_breaker": "switchgear",
            "server_rack": "server",
            "hvac_unit": "hvac",
            "cooling_fan": "hvac",
        }
        return mapping.get(class_name, "general")

    def track_temperature(
        self,
        region_id: str,
        temperature: float,
    ) -> dict:
        """
        Track temperature over time for trend analysis.

        Args:
            region_id: Unique identifier for the region
            temperature: Current temperature reading

        Returns:
            Trend analysis
        """
        if region_id not in self._temp_history:
            self._temp_history[region_id] = []

        history = self._temp_history[region_id]
        history.append(temperature)

        if len(history) > self._max_history:
            history.pop(0)

        # Calculate trend
        if len(history) >= 5:
            recent = history[-5:]
            trend = recent[-1] - recent[0]

            return {
                "current": temperature,
                "min": min(history),
                "max": max(history),
                "mean": np.mean(history),
                "trend": trend,
                "trend_direction": "rising" if trend > 1 else "falling" if trend < -1 else "stable",
                "samples": len(history),
            }

        return {
            "current": temperature,
            "samples": len(history),
            "trend": 0,
            "trend_direction": "unknown",
        }

    def create_thermal_overlay(
        self,
        rgb_image: NDArray,
        temp_map: NDArray,
        alpha: float = 0.5,
        show_hotspots: bool = True,
    ) -> NDArray:
        """
        Create RGB + thermal overlay visualization.

        Args:
            rgb_image: Original RGB image (aligned with thermal)
            temp_map: Temperature map
            alpha: Overlay transparency
            show_hotspots: Whether to highlight hotspots

        Returns:
            Blended visualization image
        """
        # Normalize temp map to 0-255
        temp_normalized = (temp_map - temp_map.min()) / (temp_map.max() - temp_map.min() + 1e-6)
        temp_uint8 = (temp_normalized * 255).astype(np.uint8)

        # Apply colormap
        thermal_colored = cv2.applyColorMap(temp_uint8, cv2.COLORMAP_INFERNO)

        # Resize if needed
        if thermal_colored.shape[:2] != rgb_image.shape[:2]:
            thermal_colored = cv2.resize(thermal_colored, (rgb_image.shape[1], rgb_image.shape[0]))

        # Blend
        overlay = cv2.addWeighted(rgb_image, 1 - alpha, thermal_colored, alpha, 0)

        # Highlight hotspots
        if show_hotspots:
            reading = self.analyze(temp_map)
            for x, y in reading.hotspot_locations:
                # Scale coordinates if needed
                scale_x = rgb_image.shape[1] / temp_map.shape[1]
                scale_y = rgb_image.shape[0] / temp_map.shape[0]
                px, py = int(x * scale_x), int(y * scale_y)

                cv2.circle(overlay, (px, py), 10, (0, 0, 255), 2)
                cv2.circle(overlay, (px, py), 3, (0, 0, 255), -1)

        return overlay

    def generate_thermal_report(
        self,
        thermal_reading: ThermalReading,
        equipment_regions: Optional[list[dict]] = None,
    ) -> dict:
        """
        Generate comprehensive thermal analysis report.

        Args:
            thermal_reading: Main thermal reading
            equipment_regions: List of equipment regions with analysis

        Returns:
            Report dictionary
        """
        report = {
            "summary": {
                "min_temperature": thermal_reading.min_temp,
                "max_temperature": thermal_reading.max_temp,
                "mean_temperature": thermal_reading.mean_temp,
                "temperature_range": thermal_reading.delta_t,
                "hotspot_count": len(thermal_reading.hotspot_locations),
                "coldspot_count": len(thermal_reading.coldspot_locations),
            },
            "assessment": self._generate_assessment(thermal_reading),
            "hotspots": [],
            "equipment_analysis": [],
        }

        # Add hotspot details
        for i, (x, y) in enumerate(thermal_reading.hotspot_locations):
            temp = thermal_reading.temperature_map[y, x]
            report["hotspots"].append({
                "id": i + 1,
                "location": (x, y),
                "temperature": float(temp),
                "delta_from_ambient": float(temp - self.baseline_temp),
            })

        # Add equipment analysis
        if equipment_regions:
            for region in equipment_regions:
                report["equipment_analysis"].append(region)

        return report

    def _generate_assessment(self, thermal_reading: ThermalReading) -> str:
        """Generate text assessment of thermal conditions."""
        assessments = []

        # Overall temperature assessment
        if thermal_reading.max_temp > 100:
            assessments.append("CRITICAL: Extreme temperature detected. Immediate attention required.")
        elif thermal_reading.max_temp > 80:
            assessments.append("WARNING: High temperature detected. Schedule inspection.")
        elif thermal_reading.max_temp > 60:
            assessments.append("ATTENTION: Elevated temperature detected. Monitor closely.")
        else:
            assessments.append("Normal operating temperatures observed.")

        # Hotspot assessment
        hotspot_count = len(thermal_reading.hotspot_locations)
        if hotspot_count > 5:
            assessments.append(f"Multiple hotspots ({hotspot_count}) detected. Comprehensive review recommended.")
        elif hotspot_count > 0:
            assessments.append(f"{hotspot_count} hotspot(s) identified for further investigation.")

        # Temperature differential
        if thermal_reading.delta_t > 40:
            assessments.append("Significant temperature differential observed. Check for load imbalance.")
        elif thermal_reading.delta_t > 20:
            assessments.append("Moderate temperature variation detected.")

        return " ".join(assessments)
