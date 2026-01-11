"""
Financial Analyzer - Solar project financial modeling.

Calculates:
- LCOE (Levelized Cost of Energy)
- NPV (Net Present Value)
- IRR (Internal Rate of Return)
- Payback Period
- PPA pricing analysis
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import math

from loguru import logger

from paces.core.types import (
    Parcel,
    ProjectFinancials,
    SolarResource,
    GridConnection,
)


@dataclass
class FinancialAssumptions:
    """Financial modeling assumptions."""
    # Capacity
    capacity_mw_dc: float = 5.0
    dc_ac_ratio: float = 1.3

    # Capital costs ($/W DC)
    module_cost_per_w: float = 0.25
    inverter_cost_per_w: float = 0.05
    bos_cost_per_w: float = 0.15
    labor_cost_per_w: float = 0.10
    soft_cost_per_w: float = 0.10

    # Additional costs
    interconnection_cost: float = 500_000
    land_cost_per_acre: float = 5_000
    contingency_pct: float = 0.10

    # Operating costs ($/kW-yr)
    om_cost_per_kw: float = 12.0
    insurance_per_kw: float = 3.0
    land_lease_per_acre: float = 1_000
    property_tax_rate: float = 0.015

    # Production
    capacity_factor: float = 0.25
    degradation_rate: float = 0.005

    # Financials
    project_life_years: int = 30
    discount_rate: float = 0.08
    inflation_rate: float = 0.025
    tax_rate: float = 0.21

    # Incentives
    itc_rate: float = 0.30
    itc_eligible: bool = True
    macrs_years: int = 5

    # Revenue
    ppa_price_kwh: float = 0.035
    ppa_escalator: float = 0.01
    ppa_term_years: int = 20


class FinancialAnalyzer:
    """
    Solar project financial analyzer.

    Provides comprehensive financial modeling including:
    - Capital cost estimation
    - Operating cost projection
    - Revenue forecasting
    - Key metrics (LCOE, NPV, IRR)
    - Sensitivity analysis
    """

    def __init__(self):
        self.assumptions = FinancialAssumptions()

    def analyze(
        self,
        parcel: Parcel,
        grid_connection: GridConnection = None,
        solar_resource: SolarResource = None,
        assumptions: FinancialAssumptions = None,
    ) -> ProjectFinancials:
        """
        Perform complete financial analysis for a solar project.

        Args:
            parcel: Target parcel
            grid_connection: Grid analysis results
            solar_resource: Solar resource data
            assumptions: Financial assumptions (uses defaults if not provided)

        Returns:
            ProjectFinancials with complete analysis
        """
        a = assumptions or self.assumptions

        # Calculate project size based on land
        usable_acres = parcel.usable_acreage or parcel.acreage * 0.8
        max_capacity_from_land = usable_acres / 6  # ~6 acres per MW

        capacity_mw_dc = min(a.capacity_mw_dc, max_capacity_from_land)
        capacity_mw_ac = capacity_mw_dc / a.dc_ac_ratio

        # Calculate CAPEX
        capacity_w_dc = capacity_mw_dc * 1_000_000

        module_cost = capacity_w_dc * a.module_cost_per_w
        inverter_cost = capacity_w_dc * a.inverter_cost_per_w
        bos_cost = capacity_w_dc * a.bos_cost_per_w
        labor_cost = capacity_w_dc * a.labor_cost_per_w
        soft_cost = capacity_w_dc * a.soft_cost_per_w

        land_cost = usable_acres * a.land_cost_per_acre
        interconnection_cost = grid_connection.estimated_total_cost if grid_connection else a.interconnection_cost

        subtotal = module_cost + inverter_cost + bos_cost + labor_cost + soft_cost + land_cost + interconnection_cost
        contingency = subtotal * a.contingency_pct
        total_capex = subtotal + contingency

        capex_per_watt = total_capex / capacity_w_dc

        # Calculate OPEX
        capacity_kw = capacity_mw_dc * 1_000
        om_cost = capacity_kw * a.om_cost_per_kw
        insurance = capacity_kw * a.insurance_per_kw
        land_lease = usable_acres * a.land_lease_per_acre
        property_tax = total_capex * a.property_tax_rate

        total_opex = om_cost + insurance + land_lease + property_tax

        # Calculate production
        if solar_resource and solar_resource.capacity_factor_1axis > 0:
            capacity_factor = solar_resource.capacity_factor_1axis
        else:
            capacity_factor = a.capacity_factor

        annual_production = capacity_mw_dc * 8760 * capacity_factor * 1000  # MWh -> kWh

        # Calculate ITC
        itc_value = 0
        if a.itc_eligible:
            itc_value = total_capex * a.itc_rate

        # Calculate NPV and cash flows
        cash_flows = [-total_capex]
        cumulative_production = 0

        for year in range(1, a.project_life_years + 1):
            # Degraded production
            degraded_production = annual_production * ((1 - a.degradation_rate) ** year)
            cumulative_production += degraded_production

            # Escalated PPA price
            if year <= a.ppa_term_years:
                price = a.ppa_price_kwh * ((1 + a.ppa_escalator) ** (year - 1))
            else:
                # After PPA, assume merchant pricing
                price = a.ppa_price_kwh * ((1 + a.ppa_escalator) ** a.ppa_term_years) * 0.8

            revenue = degraded_production * price

            # Inflated OPEX
            opex = total_opex * ((1 + a.inflation_rate) ** (year - 1))

            # ITC in year 1
            itc_benefit = itc_value if year == 1 else 0

            # Cash flow
            cf = revenue - opex + itc_benefit
            cash_flows.append(cf)

        # Calculate NPV
        npv = sum(cf / ((1 + a.discount_rate) ** i) for i, cf in enumerate(cash_flows))

        # Calculate IRR
        irr = self._calculate_irr(cash_flows)

        # Calculate payback
        cumulative = 0
        payback = a.project_life_years
        for year, cf in enumerate(cash_flows):
            cumulative += cf
            if cumulative >= 0 and payback == a.project_life_years:
                payback = year

        # Calculate LCOE
        total_cost_pv = total_capex + sum(
            (total_opex * ((1 + a.inflation_rate) ** (i - 1))) / ((1 + a.discount_rate) ** i)
            for i in range(1, a.project_life_years + 1)
        )

        total_production_pv = sum(
            (annual_production * ((1 - a.degradation_rate) ** i)) / ((1 + a.discount_rate) ** i)
            for i in range(1, a.project_life_years + 1)
        )

        lcoe = (total_cost_pv - itc_value) / total_production_pv if total_production_pv > 0 else 0

        return ProjectFinancials(
            project_id=parcel.id,
            capacity_mw_dc=capacity_mw_dc,
            capacity_mw_ac=capacity_mw_ac,
            module_cost=module_cost,
            inverter_cost=inverter_cost,
            bos_cost=bos_cost,
            labor_cost=labor_cost,
            interconnection_cost=interconnection_cost,
            land_cost=land_cost,
            development_cost=soft_cost,
            contingency=contingency,
            total_capex=total_capex,
            capex_per_watt=capex_per_watt,
            om_cost_annual=om_cost,
            om_cost_per_kw=a.om_cost_per_kw,
            insurance_annual=insurance,
            land_lease_annual=land_lease,
            property_tax_annual=property_tax,
            total_opex_annual=total_opex,
            ppa_price_kwh=a.ppa_price_kwh,
            ppa_escalator_pct=a.ppa_escalator * 100,
            ppa_term_years=a.ppa_term_years,
            annual_production_mwh=annual_production / 1000,
            degradation_rate_pct=a.degradation_rate * 100,
            npv=npv,
            irr=irr,
            payback_years=payback,
            lcoe=lcoe,
            itc_eligible=a.itc_eligible,
            itc_rate=a.itc_rate,
            itc_value=itc_value,
        )

    def _calculate_irr(self, cash_flows: list[float], guess: float = 0.1) -> float:
        """Calculate Internal Rate of Return using Newton-Raphson."""
        rate = guess

        for _ in range(100):
            npv = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))
            npv_derivative = sum(
                -i * cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows)
            )

            if abs(npv_derivative) < 1e-10:
                break

            rate = rate - npv / npv_derivative

            if rate < -0.99:
                rate = -0.99
            if rate > 10:
                rate = guess

        return rate

    def sensitivity_analysis(
        self,
        parcel: Parcel,
        base_assumptions: FinancialAssumptions,
        variable: str,
        range_pct: float = 0.20,
        steps: int = 5,
    ) -> list[dict]:
        """
        Perform sensitivity analysis on a variable.

        Args:
            parcel: Target parcel
            base_assumptions: Base case assumptions
            variable: Variable to vary (e.g., 'ppa_price_kwh', 'capacity_factor')
            range_pct: +/- range as percentage
            steps: Number of steps in each direction

        Returns:
            List of results at each sensitivity point
        """
        results = []
        base_value = getattr(base_assumptions, variable)

        for i in range(-steps, steps + 1):
            pct_change = i * (range_pct / steps)
            test_value = base_value * (1 + pct_change)

            # Create modified assumptions
            test_assumptions = FinancialAssumptions(**{
                k: v for k, v in base_assumptions.__dict__.items()
            })
            setattr(test_assumptions, variable, test_value)

            # Run analysis
            financials = self.analyze(parcel, assumptions=test_assumptions)

            results.append({
                "variable": variable,
                "base_value": base_value,
                "test_value": test_value,
                "pct_change": pct_change * 100,
                "npv": financials.npv,
                "irr": financials.irr,
                "lcoe": financials.lcoe,
            })

        return results

    def calculate_min_ppa_price(
        self,
        parcel: Parcel,
        target_irr: float = 0.10,
        grid_connection: GridConnection = None,
    ) -> float:
        """Calculate minimum PPA price to achieve target IRR."""
        low = 0.01
        high = 0.20

        for _ in range(50):
            mid = (low + high) / 2

            assumptions = FinancialAssumptions(ppa_price_kwh=mid)
            financials = self.analyze(parcel, grid_connection, assumptions=assumptions)

            if abs(financials.irr - target_irr) < 0.001:
                return mid

            if financials.irr < target_irr:
                low = mid
            else:
                high = mid

        return (low + high) / 2
