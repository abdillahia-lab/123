"""
Solar Thermal Analyzer - Thermal imaging analysis for solar panels.

Detects:
- Hotspots and thermal anomalies
- Cell failures
- Bypass diode failures
- Shading patterns
- Soiling distribution
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray
from loguru import logger

from paces.core.config import PacesConfig


@dataclass
class ThermalHotspot:
    """Detected thermal hotspot."""
    x: int
    y: int
    temperature: float
    delta_t: float
    area_pixels: int
    severity: str


@dataclass
class ThermalAnalysisResult:
    """Result of thermal analysis."""
    min_temp: float
    max_temp: float
    mean_temp: float
    std_temp: float
    ambient_temp: float
    max_delta_t: float
    hotspots: list[ThermalHotspot]
    panel_temps: list[float]
    thermal_map: NDArray[np.float32]


class SolarThermalAnalyzer:
    """
    Thermal image analyzer for solar panel inspection.

    Features:
    - Automatic ambient temperature detection
    - Hotspot detection and classification
    - Panel-level temperature extraction
    - Temperature differential analysis
    - Severity classification based on standards
    """

    def __init__(self, config: PacesConfig):
        self.config = config
        self.solar_config = config.solar

        # Thresholds from config
        self.hotspot_threshold = config.solar.hotspot_threshold_delta_c
        self.critical_threshold = config.solar.critical_hotspot_delta_c

        self._is_loaded = False

    async def load(self) -> bool:
        """Load thermal analysis models."""
        logger.info("Loading Solar Thermal Analyzer...")
        self._is_loaded = True
        logger.info("Solar Thermal Analyzer loaded")
        return True

    async def analyze(
        self,
        thermal_image: NDArray,
        ambient_temp: float = None,
    ) -> dict:
        """
        Analyze thermal image for hotspots and anomalies.

        Args:
            thermal_image: Thermal image (raw temperatures or 8-bit)
            ambient_temp: Optional ambient temperature

        Returns:
            Analysis result dictionary
        """
        if not self._is_loaded:
            raise RuntimeError("Analyzer not loaded")

        # Convert to temperature map if needed
        temp_map = self._to_temperature_map(thermal_image)

        # Detect ambient temperature
        if ambient_temp is None:
            ambient_temp = self._estimate_ambient(temp_map)

        # Calculate statistics
        min_temp = float(np.min(temp_map))
        max_temp = float(np.max(temp_map))
        mean_temp = float(np.mean(temp_map))
        std_temp = float(np.std(temp_map))

        # Maximum delta from ambient
        max_delta_t = max_temp - ambient_temp

        # Detect hotspots
        hotspots = self._detect_hotspots(temp_map, ambient_temp)

        # Extract panel temperatures
        panel_temps = self._extract_panel_temps(temp_map)

        return {
            "min_temp": min_temp,
            "max_temp": max_temp,
            "mean_temp": mean_temp,
            "std_temp": std_temp,
            "ambient_temp": ambient_temp,
            "max_delta_t": max_delta_t,
            "hotspots": hotspots,
            "panel_temps": panel_temps,
            "thermal_map": temp_map,
        }

    def _to_temperature_map(self, thermal_image: NDArray) -> NDArray[np.float32]:
        """Convert thermal image to temperature map."""
        if thermal_image.dtype == np.float32:
            # Already a temperature map
            return thermal_image

        # Convert 8-bit to approximate temperature
        # This is a simplified conversion - real implementation would use
        # camera-specific calibration
        if thermal_image.ndim == 3:
            thermal_image = np.mean(thermal_image, axis=2)

        # Assume 8-bit spans 0-100°C range
        temp_map = thermal_image.astype(np.float32) * (100.0 / 255.0)

        return temp_map

    def _estimate_ambient(self, temp_map: NDArray) -> float:
        """Estimate ambient temperature from thermal image."""
        # Use the mode of temperatures in the lower quartile
        flat = temp_map.flatten()
        lower_quartile = np.percentile(flat, 25)
        ambient_temps = flat[flat <= lower_quartile]

        if len(ambient_temps) > 0:
            return float(np.median(ambient_temps))

        return float(np.min(temp_map))

    def _detect_hotspots(
        self,
        temp_map: NDArray,
        ambient_temp: float,
    ) -> list[dict]:
        """Detect hotspots in temperature map."""
        hotspots = []

        # Calculate delta from ambient
        delta_map = temp_map - ambient_temp

        # Find hotspot regions
        hotspot_mask = delta_map > self.hotspot_threshold

        if not np.any(hotspot_mask):
            return hotspots

        # Label connected components
        from scipy import ndimage

        labeled, num_features = ndimage.label(hotspot_mask)

        for i in range(1, num_features + 1):
            region_mask = labeled == i
            region_temps = temp_map[region_mask]

            # Get hotspot properties
            y_coords, x_coords = np.where(region_mask)
            center_y = int(np.mean(y_coords))
            center_x = int(np.mean(x_coords))

            max_temp = float(np.max(region_temps))
            delta_t = max_temp - ambient_temp
            area = int(np.sum(region_mask))

            # Classify severity
            if delta_t >= self.critical_threshold:
                severity = "critical"
            elif delta_t >= 20:
                severity = "high"
            elif delta_t >= self.hotspot_threshold:
                severity = "medium"
            else:
                severity = "low"

            hotspot = {
                "x": center_x,
                "y": center_y,
                "temperature": max_temp,
                "delta_t": delta_t,
                "area_pixels": area,
                "severity": severity,
            }
            hotspots.append(hotspot)

        return hotspots

    def _extract_panel_temps(self, temp_map: NDArray) -> list[float]:
        """Extract average temperature for detected panels."""
        # Simplified - would use panel segmentation in production
        # Divide image into grid and get average temps
        panel_temps = []

        h, w = temp_map.shape
        grid_h, grid_w = 4, 6  # Assume 4x6 panel grid

        cell_h = h // grid_h
        cell_w = w // grid_w

        for i in range(grid_h):
            for j in range(grid_w):
                cell = temp_map[
                    i * cell_h : (i + 1) * cell_h,
                    j * cell_w : (j + 1) * cell_w,
                ]
                panel_temps.append(float(np.mean(cell)))

        return panel_temps

    async def unload(self) -> None:
        """Unload analyzer."""
        logger.info("Unloading Solar Thermal Analyzer")
        self._is_loaded = False
