"""
Grid Manager - Grid integration and power flow management.

Features:
- Grid connection monitoring
- Curtailment response
- Frequency regulation
- Power quality monitoring
- Market participation
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from loguru import logger

from paces.core.config import PacesConfig
from paces.core.types import GridConnection


@dataclass
class GridStatus:
    """Grid connection status."""
    connection_id: str
    timestamp: datetime

    # Power flow
    power_export_mw: float
    power_import_mw: float
    net_power_mw: float

    # Grid conditions
    voltage_pu: float
    frequency_hz: float
    power_factor: float

    # Curtailment
    curtailment_active: bool
    curtailment_limit_mw: float

    # Market
    spot_price_mwh: float
    grid_status: str  # normal, constrained, emergency


class GridManager:
    """
    Grid integration manager.

    Handles:
    - Real-time grid monitoring
    - Setpoint control
    - Curtailment response
    - Ancillary services
    - Market signals
    """

    def __init__(self, config: PacesConfig):
        self.config = config
        self.grid_config = config.grid

        self._connections: dict[str, GridConnection] = {}
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize grid manager."""
        logger.info("Initializing Grid Manager...")

        try:
            self._initialized = True
            logger.info("Grid Manager initialized")
            return True

        except Exception as e:
            logger.error(f"Grid Manager initialization failed: {e}")
            return False

    def register_connection(self, connection: GridConnection) -> None:
        """Register a grid connection."""
        self._connections[connection.id] = connection
        logger.info(f"Registered grid connection: {connection.name}")

    async def get_status(self, connection_id: str) -> GridStatus:
        """Get grid connection status."""
        if connection_id not in self._connections:
            raise ValueError(f"Unknown connection: {connection_id}")

        conn = self._connections[connection_id]

        net_power = conn.power_export_mw - conn.power_import_mw

        # Determine grid status
        if conn.curtailment_active:
            grid_status = "constrained"
        elif abs(conn.frequency_hz - 50) > 0.2:
            grid_status = "frequency_event"
        else:
            grid_status = "normal"

        return GridStatus(
            connection_id=connection_id,
            timestamp=datetime.now(),
            power_export_mw=conn.power_export_mw,
            power_import_mw=conn.power_import_mw,
            net_power_mw=net_power,
            voltage_pu=conn.voltage_pu,
            frequency_hz=conn.frequency_hz,
            power_factor=conn.power_factor,
            curtailment_active=conn.curtailment_active,
            curtailment_limit_mw=conn.curtailment_limit_mw,
            spot_price_mwh=conn.spot_price_mwh,
            grid_status=grid_status,
        )

    async def set_power_setpoint(
        self,
        connection_id: str,
        power_mw: float,
    ) -> bool:
        """Set power export/import setpoint."""
        if connection_id not in self._connections:
            return False

        conn = self._connections[connection_id]

        # Check limits
        if power_mw > 0:
            power_mw = min(power_mw, conn.export_limit_mw)
            conn.power_export_mw = power_mw
            conn.power_import_mw = 0
        else:
            power_mw = max(power_mw, -conn.import_limit_mw)
            conn.power_import_mw = abs(power_mw)
            conn.power_export_mw = 0

        logger.info(f"Grid {connection_id} setpoint: {power_mw:.2f} MW")
        return True

    async def handle_curtailment(
        self,
        connection_id: str,
        curtailment_mw: float,
    ) -> bool:
        """Handle grid curtailment signal."""
        if connection_id not in self._connections:
            return False

        conn = self._connections[connection_id]

        if curtailment_mw > 0:
            conn.curtailment_active = True
            conn.curtailment_limit_mw = curtailment_mw
            logger.warning(
                f"Curtailment active on {connection_id}: {curtailment_mw:.2f} MW"
            )
        else:
            conn.curtailment_active = False
            conn.curtailment_limit_mw = 0
            logger.info(f"Curtailment cleared on {connection_id}")

        return True

    async def respond_to_frequency_event(
        self,
        connection_id: str,
        frequency_hz: float,
    ) -> dict:
        """Respond to grid frequency deviation."""
        if not self.grid_config.frequency_regulation:
            return {"response": "disabled"}

        # Calculate required response
        deviation = frequency_hz - 50.0  # Nominal 50 Hz

        # Droop response: 4% droop means full response at 2 Hz deviation
        droop = 0.04
        response_pct = min(1.0, abs(deviation) / (50 * droop))

        if connection_id in self._connections:
            conn = self._connections[connection_id]
            max_response = conn.export_limit_mw * 0.1  # 10% of capacity

            if deviation > 0:
                # Over-frequency: reduce output
                power_adjustment = -max_response * response_pct
            else:
                # Under-frequency: increase output
                power_adjustment = max_response * response_pct

            return {
                "response": "active",
                "frequency_hz": frequency_hz,
                "deviation_hz": deviation,
                "power_adjustment_mw": power_adjustment,
            }

        return {"response": "no_connection"}

    async def get_market_signal(
        self,
        connection_id: str,
    ) -> dict:
        """Get current market signals."""
        if connection_id not in self._connections:
            return {}

        conn = self._connections[connection_id]

        return {
            "spot_price_mwh": conn.spot_price_mwh,
            "feed_in_tariff_mwh": conn.feed_in_tariff_mwh,
            "timestamp": datetime.now().isoformat(),
        }

    async def shutdown(self) -> None:
        """Shutdown grid manager."""
        logger.info("Shutting down Grid Manager")
