"""
Solar Performance Analyzer - Performance monitoring and analysis.

Calculates:
- Performance Ratio (PR)
- Capacity Factor
- Specific Yield
- Degradation Rate
- Loss Analysis
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from loguru import logger

from paces.core.config import PacesConfig
from paces.core.types import SolarFarm, EnergyReading, WeatherData


@dataclass
class SolarPerformanceMetrics:
    """Solar farm performance metrics."""
    period_start: datetime
    period_end: datetime
    farm_id: str

    # Energy
    energy_produced_mwh: float = 0.0
    energy_expected_mwh: float = 0.0
    energy_exported_mwh: float = 0.0
    energy_curtailed_mwh: float = 0.0

    # Key Performance Indicators
    performance_ratio: float = 0.0
    capacity_factor: float = 0.0
    specific_yield_kwh_kwp: float = 0.0
    availability: float = 0.0

    # Irradiation
    poa_irradiation_kwh_m2: float = 0.0
    ghi_irradiation_kwh_m2: float = 0.0
    peak_sun_hours: float = 0.0

    # Losses
    soiling_loss_pct: float = 0.0
    thermal_loss_pct: float = 0.0
    electrical_loss_pct: float = 0.0
    clipping_loss_pct: float = 0.0
    curtailment_loss_pct: float = 0.0
    total_loss_pct: float = 0.0

    # Inverter
    inverter_efficiency: float = 0.0
    dc_ac_ratio: float = 0.0

    # Comparison
    vs_budget_pct: float = 0.0
    vs_previous_period_pct: float = 0.0

    def to_dict(self) -> dict:
        return {
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
            },
            "farm_id": self.farm_id,
            "energy_produced_mwh": self.energy_produced_mwh,
            "performance_ratio": self.performance_ratio,
            "capacity_factor": self.capacity_factor,
            "specific_yield_kwh_kwp": self.specific_yield_kwh_kwp,
            "availability": self.availability,
            "total_loss_pct": self.total_loss_pct,
        }


class SolarPerformanceAnalyzer:
    """
    Solar farm performance analyzer.

    Calculates industry-standard KPIs and performs
    detailed loss analysis for O&M optimization.
    """

    def __init__(self, config: PacesConfig):
        self.config = config

    def calculate_metrics(
        self,
        farm: SolarFarm,
        readings: list[EnergyReading],
        weather: list[WeatherData],
        start_time: datetime,
        end_time: datetime,
    ) -> SolarPerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        if not readings:
            return SolarPerformanceMetrics(
                period_start=start_time,
                period_end=end_time,
                farm_id=farm.id,
            )

        # Energy calculations
        energy_produced = sum(r.energy_kwh for r in readings) / 1000  # MWh
        energy_exported = energy_produced  # Simplified

        # Irradiation calculations
        poa_irradiation = self._calculate_poa_irradiation(weather)
        peak_sun_hours = poa_irradiation  # kWh/m2 ≈ peak sun hours

        # Expected energy (simple model)
        expected_energy = (
            farm.dc_capacity_mw * peak_sun_hours * 0.85  # 85% reference yield
        )

        # Performance Ratio
        pr = energy_produced / expected_energy if expected_energy > 0 else 0

        # Capacity Factor
        hours = (end_time - start_time).total_seconds() / 3600
        cf = (
            energy_produced / (farm.dc_capacity_mw * hours)
            if farm.dc_capacity_mw > 0 and hours > 0
            else 0
        )

        # Specific Yield (kWh/kWp)
        sy = energy_produced * 1000 / farm.dc_capacity_mw if farm.dc_capacity_mw > 0 else 0

        # Availability
        operating_hours = sum(1 for r in readings if r.power_kw > 0)
        total_hours = len(readings)
        availability = operating_hours / total_hours if total_hours > 0 else 0

        # Loss analysis
        losses = self._analyze_losses(farm, readings, weather)

        return SolarPerformanceMetrics(
            period_start=start_time,
            period_end=end_time,
            farm_id=farm.id,
            energy_produced_mwh=energy_produced,
            energy_expected_mwh=expected_energy,
            energy_exported_mwh=energy_exported,
            performance_ratio=pr,
            capacity_factor=cf,
            specific_yield_kwh_kwp=sy,
            availability=availability,
            poa_irradiation_kwh_m2=poa_irradiation,
            peak_sun_hours=peak_sun_hours,
            **losses,
        )

    def _calculate_poa_irradiation(self, weather: list[WeatherData]) -> float:
        """Calculate Plane of Array irradiation."""
        if not weather:
            return 5.0  # Default peak sun hours

        total_ghi = sum(w.ghi for w in weather)
        # Convert W/m2 to kWh/m2 (assuming hourly data)
        poa_kwh_m2 = total_ghi / 1000

        return poa_kwh_m2

    def _analyze_losses(
        self,
        farm: SolarFarm,
        readings: list[EnergyReading],
        weather: list[WeatherData],
    ) -> dict:
        """Analyze various loss factors."""
        # Simplified loss analysis
        soiling = 2.0  # Assume 2% soiling loss
        thermal = self._calculate_thermal_loss(readings)
        electrical = 1.5  # Cable + connection losses
        clipping = self._calculate_clipping_loss(farm, readings)

        return {
            "soiling_loss_pct": soiling,
            "thermal_loss_pct": thermal,
            "electrical_loss_pct": electrical,
            "clipping_loss_pct": clipping,
            "curtailment_loss_pct": 0.0,
            "total_loss_pct": soiling + thermal + electrical + clipping,
        }

    def _calculate_thermal_loss(self, readings: list[EnergyReading]) -> float:
        """Calculate thermal loss from module temperatures."""
        if not readings:
            return 3.0

        # Temperature coefficient typically -0.35%/°C for mono-Si
        temp_coeff = -0.0035

        temps = [r.module_temp_c for r in readings if r.module_temp_c is not None]
        if not temps:
            return 3.0

        avg_temp = np.mean(temps)
        stc_temp = 25.0

        thermal_loss = -temp_coeff * (avg_temp - stc_temp) * 100

        return max(0, thermal_loss)

    def _calculate_clipping_loss(
        self,
        farm: SolarFarm,
        readings: list[EnergyReading],
    ) -> float:
        """Calculate inverter clipping losses."""
        if not readings or farm.ac_capacity_mw == 0:
            return 0.0

        ac_capacity_kw = farm.ac_capacity_mw * 1000
        clipped_energy = 0.0
        total_energy = 0.0

        for r in readings:
            total_energy += r.power_kw
            if r.power_kw >= ac_capacity_kw * 0.99:
                # Estimate clipped energy
                clipped_energy += r.power_kw * 0.05  # Assume 5% clipping when at limit

        if total_energy > 0:
            return (clipped_energy / total_energy) * 100

        return 0.0

    def calculate_degradation_rate(
        self,
        historical_metrics: list[SolarPerformanceMetrics],
    ) -> float:
        """Calculate annual degradation rate from historical data."""
        if len(historical_metrics) < 2:
            return 0.5  # Assume typical 0.5%/year

        # Linear regression on performance ratio
        months = np.arange(len(historical_metrics))
        prs = np.array([m.performance_ratio for m in historical_metrics])

        if len(months) > 1:
            slope, _ = np.polyfit(months, prs, 1)
            # Convert monthly slope to annual percentage
            annual_degradation = -slope * 12 * 100
            return max(0, annual_degradation)

        return 0.5
