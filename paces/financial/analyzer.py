"""
Financial Analyzer - Renewable energy financial analytics.

Features:
- Revenue tracking and forecasting
- Cost analysis
- ROI and NPV calculations
- LCOE computation
- PPA management
- Financial reporting
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from loguru import logger

from paces.core.config import PacesConfig
from paces.core.types import FinancialMetrics, Portfolio


@dataclass
class ROIAnalysis:
    """Return on Investment analysis."""
    asset_id: str
    analysis_date: datetime
    investment_lifetime_years: int

    # Investment
    capex: float
    opex_annual: float

    # Returns
    revenue_annual: float
    carbon_revenue_annual: float

    # Metrics
    npv: float
    irr: float
    payback_years: float
    lcoe: float  # Levelized Cost of Energy ($/MWh)

    # Projections
    yearly_cash_flows: list[float] = field(default_factory=list)
    cumulative_returns: list[float] = field(default_factory=list)


@dataclass
class FinancialReport:
    """Financial performance report."""
    report_period: str
    start_date: datetime
    end_date: datetime

    # Revenue
    energy_revenue: float = 0.0
    capacity_revenue: float = 0.0
    ancillary_revenue: float = 0.0
    carbon_revenue: float = 0.0
    total_revenue: float = 0.0

    # Costs
    maintenance_cost: float = 0.0
    insurance_cost: float = 0.0
    land_lease: float = 0.0
    grid_charges: float = 0.0
    admin_cost: float = 0.0
    total_cost: float = 0.0

    # Profitability
    gross_profit: float = 0.0
    ebitda: float = 0.0
    net_income: float = 0.0

    # Production
    energy_produced_mwh: float = 0.0
    avg_price_mwh: float = 0.0

    # KPIs
    capacity_factor: float = 0.0
    availability: float = 0.0
    profit_margin: float = 0.0


class FinancialAnalyzer:
    """
    Renewable energy financial analyzer.

    Provides:
    - Real-time financial tracking
    - ROI and NPV calculations
    - LCOE computation
    - Financial forecasting
    - Budget vs actual analysis
    """

    def __init__(self, config: PacesConfig):
        self.config = config
        self.financial_config = config.financial

        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize financial analyzer."""
        logger.info("Initializing Financial Analyzer...")

        try:
            self._initialized = True
            logger.info("Financial Analyzer initialized")
            return True

        except Exception as e:
            logger.error(f"Financial Analyzer initialization failed: {e}")
            return False

    async def get_metrics(
        self,
        asset_id: str = None,
        period: str = "monthly",
        energy_mwh: float = None,
        revenue: float = None,
    ) -> FinancialMetrics:
        """Get financial metrics for an asset or portfolio."""
        # Calculate metrics based on inputs
        price = self.financial_config.electricity_price_mwh
        energy_revenue = (energy_mwh or 0) * price

        if revenue is None:
            revenue = energy_revenue

        return FinancialMetrics(
            timestamp=datetime.now(),
            asset_id=asset_id or "portfolio",
            period=period,
            energy_revenue=energy_revenue,
            total_revenue=revenue,
            energy_produced_mwh=energy_mwh or 0,
            avg_price_mwh=price,
        )

    async def calculate_roi(
        self,
        asset_id: str,
        capex: float = None,
        opex_annual: float = None,
        revenue_annual: float = None,
        capacity_mw: float = None,
        capacity_factor: float = None,
        years: int = 25,
    ) -> ROIAnalysis:
        """
        Calculate comprehensive ROI analysis.

        Args:
            asset_id: Asset identifier
            capex: Capital expenditure
            opex_annual: Annual operating costs
            revenue_annual: Annual revenue (calculated if not provided)
            capacity_mw: Installed capacity
            capacity_factor: Expected capacity factor
            years: Investment lifetime

        Returns:
            ROIAnalysis with all metrics
        """
        # Default values if not provided
        if capex is None:
            capex = (capacity_mw or 1) * 1_000_000  # $1M/MW typical
        if opex_annual is None:
            opex_annual = capex * 0.02  # 2% of capex typical

        # Calculate annual energy
        if revenue_annual is None and capacity_mw and capacity_factor:
            annual_energy_mwh = capacity_mw * 8760 * capacity_factor
            price = self.financial_config.electricity_price_mwh
            revenue_annual = annual_energy_mwh * price

        if revenue_annual is None:
            revenue_annual = capex * 0.1  # 10% return assumption

        # Annual cash flow
        annual_cash_flow = revenue_annual - opex_annual

        # Discount rate
        discount_rate = self.financial_config.discount_rate

        # Calculate NPV
        cash_flows = [-capex] + [annual_cash_flow] * years
        npv = sum(cf / (1 + discount_rate) ** i for i, cf in enumerate(cash_flows))

        # Calculate IRR (simplified - would use numerical solver)
        irr = self._calculate_irr(cash_flows)

        # Payback period
        cumulative = 0
        payback = years
        cumulative_returns = [0.0]

        for i, cf in enumerate(cash_flows):
            cumulative += cf
            cumulative_returns.append(cumulative)
            if cumulative >= 0 and payback == years:
                payback = i

        # LCOE calculation
        if capacity_mw and capacity_factor:
            annual_energy = capacity_mw * 8760 * capacity_factor
            total_costs = capex + sum(
                opex_annual / (1 + discount_rate) ** i for i in range(1, years + 1)
            )
            total_energy = sum(
                annual_energy / (1 + discount_rate) ** i for i in range(1, years + 1)
            )
            lcoe = total_costs / total_energy if total_energy > 0 else 0
        else:
            lcoe = 0

        return ROIAnalysis(
            asset_id=asset_id,
            analysis_date=datetime.now(),
            investment_lifetime_years=years,
            capex=capex,
            opex_annual=opex_annual,
            revenue_annual=revenue_annual,
            carbon_revenue_annual=0,  # Would calculate from carbon tracker
            npv=npv,
            irr=irr,
            payback_years=payback,
            lcoe=lcoe,
            yearly_cash_flows=cash_flows,
            cumulative_returns=cumulative_returns,
        )

    def _calculate_irr(self, cash_flows: list[float]) -> float:
        """Calculate Internal Rate of Return."""
        # Newton-Raphson method for IRR
        def npv(rate):
            return sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))

        def npv_derivative(rate):
            return sum(
                -i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cash_flows)
            )

        rate = 0.1  # Initial guess
        for _ in range(100):
            f = npv(rate)
            df = npv_derivative(rate)
            if abs(df) < 1e-10:
                break
            rate = rate - f / df
            if rate < -1:
                rate = -0.99
            if rate > 10:
                rate = 0.1

        return rate

    async def generate_report(
        self,
        portfolio: Portfolio,
        start_date: datetime,
        end_date: datetime,
        production_data: dict = None,
    ) -> FinancialReport:
        """Generate comprehensive financial report."""
        period = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

        # Extract production data
        energy_mwh = production_data.get("energy_mwh", 0) if production_data else 0

        # Calculate revenues
        price = self.financial_config.electricity_price_mwh
        energy_revenue = energy_mwh * price
        carbon_revenue = energy_mwh * 0.4 * 50  # 0.4 tCO2/MWh * $50/tonne

        total_revenue = energy_revenue + carbon_revenue

        # Calculate costs (simplified)
        total_capacity = portfolio.solar_capacity_mw + portfolio.wind_capacity_mw
        maintenance_cost = total_capacity * 5000  # $5k/MW/period
        insurance_cost = total_capacity * 2000
        admin_cost = total_capacity * 1000

        total_cost = maintenance_cost + insurance_cost + admin_cost

        # Profitability
        gross_profit = total_revenue - total_cost
        profit_margin = gross_profit / total_revenue if total_revenue > 0 else 0

        return FinancialReport(
            report_period=period,
            start_date=start_date,
            end_date=end_date,
            energy_revenue=energy_revenue,
            carbon_revenue=carbon_revenue,
            total_revenue=total_revenue,
            maintenance_cost=maintenance_cost,
            insurance_cost=insurance_cost,
            admin_cost=admin_cost,
            total_cost=total_cost,
            gross_profit=gross_profit,
            ebitda=gross_profit,
            net_income=gross_profit * (1 - self.financial_config.tax_rate),
            energy_produced_mwh=energy_mwh,
            avg_price_mwh=price,
            profit_margin=profit_margin,
        )

    async def forecast_revenue(
        self,
        portfolio: Portfolio,
        months: int = 12,
        price_scenario: str = "base",
    ) -> dict:
        """Forecast revenue for coming months."""
        forecasts = []
        now = datetime.now()

        # Price scenarios
        price_factors = {
            "low": 0.8,
            "base": 1.0,
            "high": 1.2,
        }
        price_factor = price_factors.get(price_scenario, 1.0)
        base_price = self.financial_config.electricity_price_mwh * price_factor

        total_capacity = portfolio.solar_capacity_mw + portfolio.wind_capacity_mw

        for i in range(months):
            month_date = now + timedelta(days=30 * i)

            # Seasonal capacity factor adjustment
            month = month_date.month
            if 4 <= month <= 9:  # Summer
                cf = 0.30
            else:
                cf = 0.20

            # Monthly energy
            hours = 30 * 24
            energy_mwh = total_capacity * hours * cf

            # Revenue
            revenue = energy_mwh * base_price

            forecasts.append({
                "month": month_date.strftime("%Y-%m"),
                "energy_mwh": energy_mwh,
                "revenue": revenue,
                "capacity_factor": cf,
            })

        return {
            "scenario": price_scenario,
            "forecasts": forecasts,
            "total_revenue": sum(f["revenue"] for f in forecasts),
            "total_energy_mwh": sum(f["energy_mwh"] for f in forecasts),
        }

    async def shutdown(self) -> None:
        """Shutdown financial analyzer."""
        logger.info("Shutting down Financial Analyzer")
