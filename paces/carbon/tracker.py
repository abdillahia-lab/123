"""
Carbon Tracker - Carbon footprint tracking and ESG reporting.

Features:
- CO2 emissions avoided calculation
- Carbon credit tracking
- Lifecycle carbon analysis
- ESG metrics and reporting
- Renewable Energy Certificates
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from loguru import logger

from paces.core.config import PacesConfig
from paces.core.types import CarbonMetrics, Portfolio


@dataclass
class ESGReport:
    """ESG performance report."""
    report_period: str
    start_date: datetime
    end_date: datetime

    # Environmental
    co2_avoided_tonnes: float = 0.0
    clean_energy_generated_mwh: float = 0.0
    grid_carbon_intensity: float = 0.0
    renewable_percentage: float = 0.0

    # Carbon credits
    carbon_credits_generated: float = 0.0
    carbon_credits_retired: float = 0.0
    carbon_credit_value: float = 0.0

    # RECs
    recs_generated: int = 0
    recs_sold: int = 0
    rec_revenue: float = 0.0

    # Lifecycle
    embodied_carbon_tonnes: float = 0.0
    net_carbon_benefit_tonnes: float = 0.0
    carbon_payback_years: float = 0.0

    # Sustainability scores
    environmental_score: float = 0.0
    social_score: float = 0.0
    governance_score: float = 0.0
    overall_esg_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "period": self.report_period,
            "co2_avoided_tonnes": self.co2_avoided_tonnes,
            "clean_energy_mwh": self.clean_energy_generated_mwh,
            "carbon_credits": self.carbon_credits_generated,
            "net_carbon_benefit": self.net_carbon_benefit_tonnes,
            "esg_score": self.overall_esg_score,
        }


class CarbonTracker:
    """
    Carbon footprint tracker and ESG reporter.

    Tracks:
    - Real-time CO2 avoidance
    - Carbon credit generation
    - RECs (Renewable Energy Certificates)
    - Lifecycle emissions
    - ESG performance metrics
    """

    def __init__(self, config: PacesConfig):
        self.config = config
        self.carbon_config = config.carbon

        # Grid emission factors by region (tCO2/MWh)
        self.emission_factors = {
            "default": 0.4,
            "us_average": 0.42,
            "us_california": 0.21,
            "us_texas": 0.38,
            "eu_average": 0.28,
            "uk": 0.25,
            "germany": 0.35,
            "france": 0.05,
            "china": 0.58,
            "india": 0.71,
            "australia": 0.70,
        }

        # Embodied carbon (tCO2/MW installed)
        self.embodied_carbon = {
            "solar_pv": 40,
            "wind_onshore": 12,
            "wind_offshore": 18,
            "battery": 100,  # per MWh
        }

        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize carbon tracker."""
        logger.info("Initializing Carbon Tracker...")

        try:
            self._initialized = True
            logger.info("Carbon Tracker initialized")
            return True

        except Exception as e:
            logger.error(f"Carbon Tracker initialization failed: {e}")
            return False

    async def get_metrics(
        self,
        asset_id: str = None,
        period: str = "daily",
        energy_mwh: float = None,
        region: str = "default",
    ) -> CarbonMetrics:
        """
        Get carbon metrics for an asset or portfolio.

        Args:
            asset_id: Asset identifier (None for portfolio)
            period: Time period (hourly, daily, monthly, yearly)
            energy_mwh: Energy generated in the period
            region: Grid region for emission factor

        Returns:
            CarbonMetrics object
        """
        # Get emission factor
        emission_factor = self.emission_factors.get(
            region, self.carbon_config.grid_emission_factor_tco2_mwh
        )

        # Calculate avoided emissions
        if energy_mwh is None:
            energy_mwh = 0.0

        co2_avoided = energy_mwh * emission_factor

        # Carbon credit value
        carbon_price = self.carbon_config.carbon_price_per_tonne
        carbon_credits = co2_avoided  # 1 credit per tonne
        carbon_revenue = carbon_credits * carbon_price

        return CarbonMetrics(
            timestamp=datetime.now(),
            asset_id=asset_id or "portfolio",
            period=period,
            co2_avoided_tonnes=co2_avoided,
            grid_emission_factor=emission_factor,
            clean_energy_mwh=energy_mwh,
            carbon_credits_earned=carbon_credits,
            carbon_price_tonne=carbon_price,
            carbon_revenue=carbon_revenue,
        )

    async def calculate_avoided_emissions(
        self,
        energy_mwh: float,
        region: str = "default",
    ) -> float:
        """Calculate CO2 emissions avoided."""
        emission_factor = self.emission_factors.get(
            region, self.carbon_config.grid_emission_factor_tco2_mwh
        )
        return energy_mwh * emission_factor

    async def calculate_embodied_carbon(
        self,
        portfolio: Portfolio,
    ) -> dict:
        """Calculate lifecycle embodied carbon for portfolio."""
        solar_carbon = sum(
            f.dc_capacity_mw * self.embodied_carbon["solar_pv"]
            for f in portfolio.solar_farms
        )

        wind_carbon = sum(
            (f.rated_capacity_kw / 1000) * self.embodied_carbon["wind_onshore"]
            for f in portfolio.wind_farms
        )

        battery_carbon = sum(
            b.energy_capacity_mwh * self.embodied_carbon["battery"]
            for b in portfolio.battery_systems
        )

        total = solar_carbon + wind_carbon + battery_carbon

        return {
            "solar_carbon_tonnes": solar_carbon,
            "wind_carbon_tonnes": wind_carbon,
            "battery_carbon_tonnes": battery_carbon,
            "total_embodied_carbon_tonnes": total,
        }

    async def calculate_carbon_payback(
        self,
        portfolio: Portfolio,
        annual_generation_mwh: float,
        region: str = "default",
    ) -> float:
        """Calculate carbon payback period in years."""
        embodied = await self.calculate_embodied_carbon(portfolio)
        total_embodied = embodied["total_embodied_carbon_tonnes"]

        annual_avoided = await self.calculate_avoided_emissions(
            annual_generation_mwh, region
        )

        if annual_avoided > 0:
            return total_embodied / annual_avoided
        return float("inf")

    async def generate_esg_report(
        self,
        portfolio: Portfolio,
        start_date: datetime,
        end_date: datetime,
        energy_data: dict = None,
    ) -> ESGReport:
        """Generate comprehensive ESG report."""
        period_days = (end_date - start_date).days
        period_name = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

        # Calculate energy metrics
        energy_mwh = energy_data.get("total_mwh", 0) if energy_data else 0

        # Carbon metrics
        co2_avoided = await self.calculate_avoided_emissions(energy_mwh)
        embodied = await self.calculate_embodied_carbon(portfolio)

        # RECs (1 REC = 1 MWh)
        recs_generated = int(energy_mwh)
        rec_price = 5.0  # $/REC average
        rec_revenue = recs_generated * rec_price

        # Carbon credits
        carbon_credits = co2_avoided
        carbon_value = carbon_credits * self.carbon_config.carbon_price_per_tonne

        # Payback period
        annual_factor = 365 / period_days if period_days > 0 else 1
        annual_generation = energy_mwh * annual_factor
        payback = await self.calculate_carbon_payback(
            portfolio, annual_generation
        )

        # ESG scores (simplified)
        environmental_score = min(100, co2_avoided / 100 + 50)
        social_score = 70  # Placeholder
        governance_score = 80  # Placeholder
        overall_score = (environmental_score + social_score + governance_score) / 3

        return ESGReport(
            report_period=period_name,
            start_date=start_date,
            end_date=end_date,
            co2_avoided_tonnes=co2_avoided,
            clean_energy_generated_mwh=energy_mwh,
            grid_carbon_intensity=self.carbon_config.grid_emission_factor_tco2_mwh,
            renewable_percentage=100.0,
            carbon_credits_generated=carbon_credits,
            carbon_credits_retired=0,
            carbon_credit_value=carbon_value,
            recs_generated=recs_generated,
            recs_sold=0,
            rec_revenue=rec_revenue,
            embodied_carbon_tonnes=embodied["total_embodied_carbon_tonnes"],
            net_carbon_benefit_tonnes=co2_avoided - embodied["total_embodied_carbon_tonnes"] / 25,  # 25 year life
            carbon_payback_years=payback,
            environmental_score=environmental_score,
            social_score=social_score,
            governance_score=governance_score,
            overall_esg_score=overall_score,
        )

    async def shutdown(self) -> None:
        """Shutdown carbon tracker."""
        logger.info("Shutting down Carbon Tracker")
