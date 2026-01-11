"""
Portfolio Optimizer - AI-driven renewable portfolio optimization.

Features:
- Multi-asset dispatch optimization
- Risk management
- Hedging strategies
- Capacity planning
- Investment optimization
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from loguru import logger

from paces.core.config import PacesConfig
from paces.core.types import Portfolio


@dataclass
class OptimizationResult:
    """Portfolio optimization result."""
    timestamp: datetime
    horizon_hours: int

    # Dispatch schedule
    solar_dispatch_mw: list[float] = field(default_factory=list)
    wind_dispatch_mw: list[float] = field(default_factory=list)
    battery_dispatch_mw: list[float] = field(default_factory=list)
    grid_exchange_mw: list[float] = field(default_factory=list)

    # Metrics
    total_revenue: float = 0.0
    total_cost: float = 0.0
    net_profit: float = 0.0
    carbon_avoided_tonnes: float = 0.0

    # Risk metrics
    value_at_risk: float = 0.0
    expected_shortfall: float = 0.0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "horizon_hours": self.horizon_hours,
            "total_revenue": self.total_revenue,
            "net_profit": self.net_profit,
            "carbon_avoided_tonnes": self.carbon_avoided_tonnes,
        }


class PortfolioOptimizer:
    """
    AI-powered portfolio optimizer.

    Optimizes:
    - Real-time dispatch across assets
    - Battery charging/discharging
    - Grid interaction
    - Revenue maximization
    - Risk management
    """

    def __init__(self, config: PacesConfig):
        self.config = config
        self._portfolio: Optional[Portfolio] = None

    def set_portfolio(self, portfolio: Portfolio) -> None:
        """Set the portfolio to optimize."""
        self._portfolio = portfolio

    async def optimize(
        self,
        solar_forecast: list[float],
        wind_forecast: list[float],
        price_forecast: list[float],
        load_forecast: list[float] = None,
        horizon_hours: int = 24,
    ) -> OptimizationResult:
        """
        Optimize portfolio dispatch.

        Args:
            solar_forecast: Expected solar generation (MW)
            wind_forecast: Expected wind generation (MW)
            price_forecast: Expected electricity prices ($/MWh)
            load_forecast: Expected load (MW)
            horizon_hours: Optimization horizon

        Returns:
            OptimizationResult with optimal dispatch
        """
        if not self._portfolio:
            raise RuntimeError("No portfolio set")

        logger.info(f"Optimizing portfolio for {horizon_hours} hours")

        # Get battery capacity
        battery_capacity_mwh = sum(
            b.energy_capacity_mwh for b in self._portfolio.battery_systems
        )
        battery_power_mw = sum(
            b.power_capacity_mw for b in self._portfolio.battery_systems
        )

        # Simple optimization: maximize revenue
        solar_dispatch = solar_forecast[:horizon_hours]
        wind_dispatch = wind_forecast[:horizon_hours]

        # Battery optimization
        battery_dispatch = []
        battery_soc = 50.0  # Start at 50%

        for i in range(horizon_hours):
            price = price_forecast[i] if i < len(price_forecast) else 50

            renewable = (
                (solar_dispatch[i] if i < len(solar_dispatch) else 0) +
                (wind_dispatch[i] if i < len(wind_dispatch) else 0)
            )

            load = load_forecast[i] if load_forecast and i < len(load_forecast) else renewable

            # Decide battery action
            if price < 40 and battery_soc < 90:
                # Charge from cheap grid
                charge = min(battery_power_mw, (90 - battery_soc) / 100 * battery_capacity_mwh)
                battery_dispatch.append(charge)
                battery_soc += charge / battery_capacity_mwh * 100
            elif price > 70 and battery_soc > 20:
                # Discharge to grid
                discharge = min(battery_power_mw, (battery_soc - 20) / 100 * battery_capacity_mwh)
                battery_dispatch.append(-discharge)
                battery_soc -= discharge / battery_capacity_mwh * 100
            else:
                battery_dispatch.append(0)

        # Grid exchange = generation + battery - load
        grid_exchange = []
        for i in range(horizon_hours):
            solar = solar_dispatch[i] if i < len(solar_dispatch) else 0
            wind = wind_dispatch[i] if i < len(wind_dispatch) else 0
            battery = battery_dispatch[i] if i < len(battery_dispatch) else 0
            load = load_forecast[i] if load_forecast and i < len(load_forecast) else 0

            grid_exchange.append(solar + wind - battery - load)

        # Calculate revenue
        revenue = sum(
            max(0, grid_exchange[i]) * price_forecast[i]
            for i in range(min(horizon_hours, len(price_forecast)))
        )

        # Calculate costs (import)
        cost = sum(
            abs(min(0, grid_exchange[i])) * price_forecast[i]
            for i in range(min(horizon_hours, len(price_forecast)))
        )

        # Carbon avoided
        total_generation = sum(solar_dispatch) + sum(wind_dispatch)
        carbon_avoided = total_generation * 0.4  # 0.4 tCO2/MWh grid factor

        return OptimizationResult(
            timestamp=datetime.now(),
            horizon_hours=horizon_hours,
            solar_dispatch_mw=solar_dispatch,
            wind_dispatch_mw=wind_dispatch,
            battery_dispatch_mw=battery_dispatch,
            grid_exchange_mw=grid_exchange,
            total_revenue=revenue,
            total_cost=cost,
            net_profit=revenue - cost,
            carbon_avoided_tonnes=carbon_avoided,
        )

    async def analyze_risk(
        self,
        forecast_scenarios: list[dict],
        price_scenarios: list[list[float]],
    ) -> dict:
        """Analyze portfolio risk across scenarios."""
        profits = []

        for i, scenario in enumerate(forecast_scenarios):
            prices = price_scenarios[i] if i < len(price_scenarios) else price_scenarios[0]

            result = await self.optimize(
                solar_forecast=scenario.get("solar", []),
                wind_forecast=scenario.get("wind", []),
                price_forecast=prices,
            )
            profits.append(result.net_profit)

        profits = np.array(profits)

        return {
            "expected_profit": float(np.mean(profits)),
            "profit_std": float(np.std(profits)),
            "var_95": float(np.percentile(profits, 5)),
            "var_99": float(np.percentile(profits, 1)),
            "expected_shortfall": float(np.mean(profits[profits < np.percentile(profits, 5)])),
            "best_case": float(np.max(profits)),
            "worst_case": float(np.min(profits)),
        }

    async def recommend_investments(
        self,
        budget: float,
        options: list[dict],
    ) -> list[dict]:
        """Recommend investment options."""
        scored_options = []

        for option in options:
            # Calculate NPV, IRR, payback period
            capex = option.get("capex", 0)
            annual_revenue = option.get("annual_revenue", 0)
            opex = option.get("annual_opex", 0)
            lifetime = option.get("lifetime_years", 25)

            # Simple NPV calculation
            discount_rate = self.config.financial.discount_rate
            cash_flows = [-capex] + [(annual_revenue - opex)] * lifetime
            npv = sum(cf / (1 + discount_rate) ** i for i, cf in enumerate(cash_flows))

            # Payback period
            cumulative = 0
            payback = lifetime
            for i, cf in enumerate(cash_flows):
                cumulative += cf
                if cumulative >= 0:
                    payback = i
                    break

            scored_options.append({
                **option,
                "npv": npv,
                "payback_years": payback,
                "score": npv / capex if capex > 0 else 0,
            })

        # Rank by score
        scored_options.sort(key=lambda x: x["score"], reverse=True)

        # Select within budget
        selected = []
        remaining_budget = budget

        for option in scored_options:
            if option["capex"] <= remaining_budget:
                selected.append(option)
                remaining_budget -= option["capex"]

        return selected
