"""
Wind Performance Analyzer - Performance monitoring and power curve analysis.

Calculates:
- Capacity Factor
- Availability
- Power Curve Analysis
- Wake Loss Estimation
- Performance Trends
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from loguru import logger

from paces.core.config import PacesConfig
from paces.core.types import WindTurbine, WindFarm, EnergyReading, WeatherData


@dataclass
class WindPerformanceMetrics:
    """Wind farm performance metrics."""
    period_start: datetime
    period_end: datetime
    farm_id: str

    # Energy
    energy_produced_mwh: float = 0.0
    energy_expected_mwh: float = 0.0
    energy_curtailed_mwh: float = 0.0

    # KPIs
    capacity_factor: float = 0.0
    availability: float = 0.0
    performance_ratio: float = 0.0

    # Wind conditions
    avg_wind_speed_ms: float = 0.0
    max_wind_speed_ms: float = 0.0
    wind_direction_variability: float = 0.0

    # Turbine status
    turbines_online: int = 0
    turbines_total: int = 0
    turbines_in_maintenance: int = 0

    # Losses
    wake_loss_pct: float = 0.0
    curtailment_loss_pct: float = 0.0
    downtime_loss_pct: float = 0.0
    total_loss_pct: float = 0.0

    def to_dict(self) -> dict:
        return {
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
            },
            "farm_id": self.farm_id,
            "energy_produced_mwh": self.energy_produced_mwh,
            "capacity_factor": self.capacity_factor,
            "availability": self.availability,
            "avg_wind_speed_ms": self.avg_wind_speed_ms,
            "turbines_online": self.turbines_online,
            "total_loss_pct": self.total_loss_pct,
        }


class WindPerformanceAnalyzer:
    """
    Wind farm performance analyzer.

    Features:
    - Power curve analysis
    - Capacity factor calculation
    - Wake loss estimation
    - Yaw misalignment detection
    - Underperformance identification
    """

    def __init__(self, config: PacesConfig):
        self.config = config

    def calculate_metrics(
        self,
        farm: WindFarm,
        readings: list[EnergyReading],
        weather: list[WeatherData],
        start_time: datetime,
        end_time: datetime,
    ) -> WindPerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        if not readings:
            return WindPerformanceMetrics(
                period_start=start_time,
                period_end=end_time,
                farm_id=farm.id,
                turbines_total=len(farm.turbines),
            )

        # Energy calculations
        energy_produced = sum(r.energy_kwh for r in readings) / 1000  # MWh

        # Capacity factor
        hours = (end_time - start_time).total_seconds() / 3600
        rated_capacity_mw = sum(t.rated_capacity_kw for t in farm.turbines) / 1000
        cf = (
            energy_produced / (rated_capacity_mw * hours)
            if rated_capacity_mw > 0 and hours > 0
            else 0
        )

        # Availability
        total_readings = len(readings)
        operating_readings = sum(1 for r in readings if r.power_kw > 0)
        availability = operating_readings / total_readings if total_readings > 0 else 0

        # Wind conditions
        wind_speeds = [r.wind_speed_ms for r in readings if r.wind_speed_ms is not None]
        avg_wind = np.mean(wind_speeds) if wind_speeds else 0
        max_wind = np.max(wind_speeds) if wind_speeds else 0

        # Expected energy from power curve
        expected_energy = self._calculate_expected_energy(
            farm.turbines, weather, hours
        )

        # Losses
        wake_loss = farm.wake_loss_pct
        curtailment_loss = 0.0  # Would come from grid data
        downtime_loss = (1 - availability) * 100

        # Turbine status
        turbines_online = sum(
            1 for t in farm.turbines
            if t.status.value == "operational"
        )

        return WindPerformanceMetrics(
            period_start=start_time,
            period_end=end_time,
            farm_id=farm.id,
            energy_produced_mwh=energy_produced,
            energy_expected_mwh=expected_energy,
            capacity_factor=cf,
            availability=availability,
            performance_ratio=energy_produced / expected_energy if expected_energy > 0 else 0,
            avg_wind_speed_ms=avg_wind,
            max_wind_speed_ms=max_wind,
            turbines_online=turbines_online,
            turbines_total=len(farm.turbines),
            wake_loss_pct=wake_loss,
            curtailment_loss_pct=curtailment_loss,
            downtime_loss_pct=downtime_loss,
            total_loss_pct=wake_loss + curtailment_loss + downtime_loss,
        )

    def _calculate_expected_energy(
        self,
        turbines: list[WindTurbine],
        weather: list[WeatherData],
        hours: float,
    ) -> float:
        """Calculate expected energy from power curve."""
        if not turbines or not weather:
            return 0.0

        total_energy = 0.0

        for turbine in turbines:
            for w in weather:
                # Power from wind speed using cubic relationship
                power = turbine.calculate_power_output(w.wind_speed_ms)
                # Convert to MWh (assuming hourly weather data)
                total_energy += power / 1000000

        return total_energy

    def analyze_power_curve(
        self,
        turbine: WindTurbine,
        readings: list[EnergyReading],
    ) -> dict:
        """Analyze turbine power curve deviation."""
        if not readings:
            return {"status": "insufficient_data"}

        # Extract wind-power pairs
        wind_speeds = []
        powers = []

        for r in readings:
            if r.wind_speed_ms is not None and r.power_kw is not None:
                wind_speeds.append(r.wind_speed_ms)
                powers.append(r.power_kw)

        if len(wind_speeds) < 10:
            return {"status": "insufficient_data"}

        wind_speeds = np.array(wind_speeds)
        powers = np.array(powers)

        # Bin by wind speed
        bins = np.arange(0, 26, 1)
        actual_curve = []
        expected_curve = []

        for i in range(len(bins) - 1):
            mask = (wind_speeds >= bins[i]) & (wind_speeds < bins[i + 1])
            if np.sum(mask) > 0:
                actual_power = np.mean(powers[mask])
                expected_power = turbine.calculate_power_output(bins[i] + 0.5)
                actual_curve.append(actual_power)
                expected_curve.append(expected_power)

        # Calculate deviation
        actual_curve = np.array(actual_curve)
        expected_curve = np.array(expected_curve)

        if len(actual_curve) > 0 and np.sum(expected_curve) > 0:
            deviation_pct = (
                (np.sum(expected_curve) - np.sum(actual_curve))
                / np.sum(expected_curve) * 100
            )
        else:
            deviation_pct = 0

        status = "normal"
        if deviation_pct > 10:
            status = "underperforming"
        elif deviation_pct > 5:
            status = "slight_underperformance"
        elif deviation_pct < -5:
            status = "overperforming"

        return {
            "status": status,
            "deviation_pct": deviation_pct,
            "wind_bins": bins[:-1].tolist(),
            "actual_curve": actual_curve.tolist(),
            "expected_curve": expected_curve.tolist(),
        }

    def detect_yaw_misalignment(
        self,
        turbine: WindTurbine,
        readings: list[EnergyReading],
    ) -> dict:
        """Detect yaw misalignment from production data."""
        # Simplified analysis - would use nacelle-mounted anemometer data
        if turbine.yaw_angle_deg > self.config.wind.yaw_misalignment_threshold_deg:
            return {
                "misaligned": True,
                "yaw_error_deg": turbine.yaw_angle_deg,
                "estimated_loss_pct": turbine.yaw_angle_deg * 0.5,  # ~0.5% per degree
                "recommendation": "Calibrate yaw position sensor and check yaw motor",
            }

        return {
            "misaligned": False,
            "yaw_error_deg": 0,
            "estimated_loss_pct": 0,
        }
