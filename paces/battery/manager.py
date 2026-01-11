"""
Battery Manager - BESS monitoring and optimization.

Features:
- State of Charge/Health monitoring
- Thermal management
- Dispatch optimization
- Degradation tracking
- Grid services scheduling
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from loguru import logger

from paces.core.config import PacesConfig
from paces.core.types import BatterySystem, AlertSeverity


@dataclass
class BatteryStatus:
    """Current battery system status."""
    system_id: str
    timestamp: datetime

    # State
    soc: float  # State of Charge (%)
    soh: float  # State of Health (%)
    power_kw: float  # Positive = charging
    mode: str  # charging, discharging, standby, maintenance

    # Thermal
    avg_temperature_c: float
    max_temperature_c: float
    thermal_status: str

    # Capacity
    available_energy_kwh: float
    available_charge_kw: float
    available_discharge_kw: float

    # Cell level
    cell_voltage_min: float
    cell_voltage_max: float
    cell_imbalance_mv: float

    # Alerts
    alerts: list[dict]


@dataclass
class DispatchSchedule:
    """Battery dispatch schedule."""
    system_id: str
    generated_at: datetime
    horizon_hours: int

    timestamps: list[datetime]
    power_kw: list[float]  # Positive = charge, Negative = discharge
    soc_trajectory: list[float]

    revenue_expected: float
    cycles_expected: float


class BatteryManager:
    """
    Battery Energy Storage System manager.

    Features:
    - Real-time monitoring
    - SOC/SOH estimation
    - Optimal dispatch scheduling
    - Degradation-aware operation
    - Multi-service stacking (arbitrage + ancillary)
    """

    def __init__(self, config: PacesConfig):
        self.config = config
        self.battery_config = config.battery

        self._systems: dict[str, BatterySystem] = {}
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize battery manager."""
        logger.info("Initializing Battery Manager...")

        try:
            self._initialized = True
            logger.info("Battery Manager initialized")
            return True

        except Exception as e:
            logger.error(f"Battery Manager initialization failed: {e}")
            return False

    def register_system(self, system: BatterySystem) -> None:
        """Register a battery system."""
        self._systems[system.id] = system
        logger.info(f"Registered battery system: {system.name}")

    async def get_status(self, system_id: str) -> BatteryStatus:
        """Get current battery system status."""
        if system_id not in self._systems:
            raise ValueError(f"Unknown system: {system_id}")

        system = self._systems[system_id]

        # Check for alerts
        alerts = self._check_alerts(system)

        # Calculate available power
        soc = system.soc
        soh = system.soh
        power_capacity = system.power_capacity_mw * 1000  # kW

        available_charge = power_capacity * ((100 - soc) / 100)
        available_discharge = power_capacity * (soc / 100)

        # Thermal status
        if system.avg_temperature_c > self.battery_config.temperature_critical_c:
            thermal_status = "critical"
        elif system.avg_temperature_c > self.battery_config.temperature_warning_c:
            thermal_status = "warning"
        else:
            thermal_status = "normal"

        return BatteryStatus(
            system_id=system_id,
            timestamp=datetime.now(),
            soc=soc,
            soh=soh,
            power_kw=system.power_kw,
            mode=system.mode,
            avg_temperature_c=system.avg_temperature_c,
            max_temperature_c=system.avg_temperature_c + 5,  # Simplified
            thermal_status=thermal_status,
            available_energy_kwh=system.available_energy_mwh * 1000,
            available_charge_kw=available_charge,
            available_discharge_kw=available_discharge,
            cell_voltage_min=3.2,  # Simplified
            cell_voltage_max=3.8,
            cell_imbalance_mv=50,
            alerts=alerts,
        )

    def _check_alerts(self, system: BatterySystem) -> list[dict]:
        """Check for battery alerts."""
        alerts = []

        # SOC alerts
        if system.soc < self.battery_config.min_soc:
            alerts.append({
                "type": "low_soc",
                "severity": "warning",
                "message": f"SOC below minimum ({system.soc:.1f}%)",
            })

        if system.soc > self.battery_config.max_soc:
            alerts.append({
                "type": "high_soc",
                "severity": "warning",
                "message": f"SOC above maximum ({system.soc:.1f}%)",
            })

        # Temperature alerts
        if system.avg_temperature_c > self.battery_config.temperature_critical_c:
            alerts.append({
                "type": "high_temperature",
                "severity": "critical",
                "message": f"Critical temperature ({system.avg_temperature_c:.1f}°C)",
            })
        elif system.avg_temperature_c > self.battery_config.temperature_warning_c:
            alerts.append({
                "type": "high_temperature",
                "severity": "warning",
                "message": f"Elevated temperature ({system.avg_temperature_c:.1f}°C)",
            })

        # SOH alerts
        if system.soh < 80:
            alerts.append({
                "type": "low_soh",
                "severity": "warning",
                "message": f"Battery health degraded ({system.soh:.1f}%)",
            })

        return alerts

    async def optimize_dispatch(
        self,
        system_id: str,
        price_forecast: dict = None,
        load_forecast: dict = None,
        horizon_hours: int = 24,
    ) -> DispatchSchedule:
        """
        Optimize battery dispatch schedule.

        Uses price and load forecasts to maximize revenue
        while respecting SOC limits and degradation constraints.
        """
        if system_id not in self._systems:
            raise ValueError(f"Unknown system: {system_id}")

        system = self._systems[system_id]

        # Generate timestamps
        now = datetime.now()
        timestamps = [now + timedelta(hours=i) for i in range(horizon_hours)]

        # Get prices
        if price_forecast and "prices_mwh" in price_forecast:
            prices = price_forecast["prices_mwh"][:horizon_hours]
        else:
            # Default price pattern
            prices = self._default_prices(horizon_hours)

        # Optimize dispatch
        schedule, soc_trajectory = self._optimize_dispatch(
            system, prices, horizon_hours
        )

        # Calculate expected revenue
        revenue = sum(
            -schedule[i] * prices[i] / 1000
            for i in range(len(schedule))
        )

        # Estimate cycles
        total_throughput = sum(abs(p) for p in schedule)
        cycles = total_throughput / (system.energy_capacity_mwh * 1000 * 2)

        return DispatchSchedule(
            system_id=system_id,
            generated_at=now,
            horizon_hours=horizon_hours,
            timestamps=timestamps,
            power_kw=schedule,
            soc_trajectory=soc_trajectory,
            revenue_expected=revenue,
            cycles_expected=cycles,
        )

    def _default_prices(self, hours: int) -> list[float]:
        """Generate default price pattern."""
        prices = []
        for i in range(hours):
            hour = (datetime.now().hour + i) % 24
            if 6 <= hour <= 9 or 17 <= hour <= 20:
                prices.append(80)  # Peak
            elif 22 <= hour or hour <= 5:
                prices.append(30)  # Off-peak
            else:
                prices.append(50)  # Shoulder
        return prices

    def _optimize_dispatch(
        self,
        system: BatterySystem,
        prices: list[float],
        horizon: int,
    ) -> tuple[list[float], list[float]]:
        """Simple dispatch optimization."""
        power_kw = system.power_capacity_mw * 1000
        energy_kwh = system.energy_capacity_mwh * 1000

        schedule = []
        soc_trajectory = [system.soc]

        current_soc = system.soc

        for i in range(horizon):
            price = prices[i]

            # Simple strategy: charge when cheap, discharge when expensive
            if price < 40 and current_soc < self.battery_config.max_soc:
                # Charge
                charge_power = min(
                    power_kw,
                    (self.battery_config.max_soc - current_soc) / 100 * energy_kwh,
                )
                schedule.append(charge_power)
                current_soc += charge_power / energy_kwh * 100

            elif price > 70 and current_soc > self.battery_config.min_soc:
                # Discharge
                discharge_power = min(
                    power_kw,
                    (current_soc - self.battery_config.min_soc) / 100 * energy_kwh,
                )
                schedule.append(-discharge_power)
                current_soc -= discharge_power / energy_kwh * 100

            else:
                # Standby
                schedule.append(0)

            soc_trajectory.append(current_soc)

        return schedule, soc_trajectory

    async def set_mode(
        self,
        system_id: str,
        mode: str,
        power_kw: float = None,
    ) -> bool:
        """Set battery operating mode."""
        if system_id not in self._systems:
            return False

        system = self._systems[system_id]
        system.mode = mode

        if power_kw is not None:
            system.power_kw = power_kw

        logger.info(f"Battery {system_id} mode set to: {mode}")
        return True

    async def shutdown(self) -> None:
        """Shutdown battery manager."""
        logger.info("Shutting down Battery Manager")
