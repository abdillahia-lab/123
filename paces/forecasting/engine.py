"""
Forecast Engine - AI-powered energy production forecasting.

Uses state-of-the-art models:
- Temporal Fusion Transformer for time series
- Weather integration from multiple providers
- Ensemble methods for robust predictions
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from loguru import logger

from paces.core.config import PacesConfig
from paces.core.types import (
    PowerForecast,
    WeatherData,
    ForecastModel,
    GeoLocation,
)


class ForecastEngine:
    """
    AI-powered energy forecasting engine.

    Features:
    - Multi-horizon forecasting (hours to days)
    - Weather-aware predictions
    - Uncertainty quantification
    - Ensemble modeling
    - Automatic model selection
    """

    def __init__(self, config: PacesConfig):
        self.config = config
        self.forecast_config = config.forecasting

        # Forecasters
        self._solar_forecaster = None
        self._wind_forecaster = None
        self._weather_service = None

        # Models
        self._tft_model = None
        self._prophet_model = None

        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize forecasting models and services."""
        logger.info("Initializing Forecast Engine...")

        try:
            from paces.forecasting.solar_forecast import SolarForecaster
            from paces.forecasting.wind_forecast import WindForecaster
            from paces.forecasting.weather import WeatherService

            # Initialize weather service first
            self._weather_service = WeatherService(self.config)
            await self._weather_service.initialize()

            # Initialize forecasters
            if self.forecast_config.solar_forecast_enabled:
                self._solar_forecaster = SolarForecaster(
                    self.config, self._weather_service
                )
                await self._solar_forecaster.initialize()

            if self.forecast_config.wind_forecast_enabled:
                self._wind_forecaster = WindForecaster(
                    self.config, self._weather_service
                )
                await self._wind_forecaster.initialize()

            self._initialized = True
            logger.info("Forecast Engine initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Forecast Engine initialization failed: {e}")
            return False

    async def forecast_solar(
        self,
        farm_id: str,
        hours: int = 48,
        include_uncertainty: bool = True,
    ) -> PowerForecast:
        """
        Generate solar power forecast.

        Args:
            farm_id: Solar farm identifier
            hours: Forecast horizon in hours
            include_uncertainty: Include confidence intervals

        Returns:
            PowerForecast with predictions
        """
        if not self._solar_forecaster:
            raise RuntimeError("Solar forecaster not initialized")

        return await self._solar_forecaster.forecast(
            farm_id=farm_id,
            horizon_hours=hours,
            include_uncertainty=include_uncertainty,
        )

    async def forecast_wind(
        self,
        farm_id: str,
        hours: int = 48,
        include_uncertainty: bool = True,
    ) -> PowerForecast:
        """
        Generate wind power forecast.

        Args:
            farm_id: Wind farm identifier
            hours: Forecast horizon in hours
            include_uncertainty: Include confidence intervals

        Returns:
            PowerForecast with predictions
        """
        if not self._wind_forecaster:
            raise RuntimeError("Wind forecaster not initialized")

        return await self._wind_forecaster.forecast(
            farm_id=farm_id,
            horizon_hours=hours,
            include_uncertainty=include_uncertainty,
        )

    async def forecast_portfolio(
        self,
        farm_ids: list[str],
        hours: int = 48,
    ) -> dict:
        """Forecast power for entire portfolio."""
        solar_forecasts = []
        wind_forecasts = []

        for farm_id in farm_ids:
            # Determine farm type from ID prefix or lookup
            if farm_id.startswith("solar_"):
                forecast = await self.forecast_solar(farm_id, hours)
                solar_forecasts.append(forecast)
            elif farm_id.startswith("wind_"):
                forecast = await self.forecast_wind(farm_id, hours)
                wind_forecasts.append(forecast)

        # Aggregate forecasts
        total_forecast = self._aggregate_forecasts(
            solar_forecasts + wind_forecasts
        )

        return {
            "solar": solar_forecasts,
            "wind": wind_forecasts,
            "total": total_forecast,
            "generated_at": datetime.now().isoformat(),
        }

    def _aggregate_forecasts(
        self,
        forecasts: list[PowerForecast],
    ) -> dict:
        """Aggregate multiple forecasts into total."""
        if not forecasts:
            return {
                "timestamps": [],
                "power_kw": [],
                "energy_kwh": [],
            }

        # Use first forecast's timestamps
        timestamps = forecasts[0].timestamps
        total_power = np.zeros(len(timestamps))
        total_energy = np.zeros(len(timestamps))
        lower_bound = np.zeros(len(timestamps))
        upper_bound = np.zeros(len(timestamps))

        for forecast in forecasts:
            for i in range(min(len(forecast.power_kw), len(total_power))):
                total_power[i] += forecast.power_kw[i]
                total_energy[i] += forecast.energy_kwh[i]
                if forecast.lower_bound_kw:
                    lower_bound[i] += forecast.lower_bound_kw[i]
                if forecast.upper_bound_kw:
                    upper_bound[i] += forecast.upper_bound_kw[i]

        return {
            "timestamps": [t.isoformat() for t in timestamps],
            "power_kw": total_power.tolist(),
            "energy_kwh": total_energy.tolist(),
            "total_energy_kwh": float(np.sum(total_energy)),
            "peak_power_kw": float(np.max(total_power)),
            "lower_bound_kw": lower_bound.tolist(),
            "upper_bound_kw": upper_bound.tolist(),
        }

    async def forecast_prices(
        self,
        hours: int = 24,
    ) -> dict:
        """Forecast electricity prices."""
        # Simplified price forecast
        # In production, would use market data and ML models

        timestamps = [
            datetime.now() + timedelta(hours=i)
            for i in range(hours)
        ]

        # Simulate daily price pattern
        prices = []
        for ts in timestamps:
            hour = ts.hour
            # Peak pricing 6-9am and 5-8pm
            if 6 <= hour <= 9 or 17 <= hour <= 20:
                base_price = 80  # Peak
            elif 22 <= hour or hour <= 5:
                base_price = 30  # Off-peak
            else:
                base_price = 50  # Shoulder

            # Add some variation
            price = base_price + np.random.normal(0, 5)
            prices.append(max(0, price))

        return {
            "timestamps": [t.isoformat() for t in timestamps],
            "prices_mwh": prices,
            "currency": self.config.financial.currency,
            "generated_at": datetime.now().isoformat(),
        }

    async def forecast_load(
        self,
        hours: int = 24,
    ) -> dict:
        """Forecast load/demand."""
        timestamps = [
            datetime.now() + timedelta(hours=i)
            for i in range(hours)
        ]

        # Simulate typical load profile
        loads = []
        for ts in timestamps:
            hour = ts.hour
            # Morning ramp, midday peak, evening peak
            if 6 <= hour <= 9:
                base_load = 70 + (hour - 6) * 10
            elif 10 <= hour <= 16:
                base_load = 100 - (hour - 10) * 2
            elif 17 <= hour <= 21:
                base_load = 90 + (hour - 17) * 5
            else:
                base_load = 50

            load = base_load + np.random.normal(0, 5)
            loads.append(max(0, load))

        return {
            "timestamps": [t.isoformat() for t in timestamps],
            "load_mw": loads,
            "generated_at": datetime.now().isoformat(),
        }

    async def get_weather(
        self,
        location: GeoLocation,
        days: int = 7,
    ) -> list[WeatherData]:
        """Get weather forecast for a location."""
        if not self._weather_service:
            raise RuntimeError("Weather service not initialized")

        return await self._weather_service.get_forecast(location, days)

    async def shutdown(self) -> None:
        """Shutdown forecast engine."""
        logger.info("Shutting down Forecast Engine")
        if self._weather_service:
            await self._weather_service.shutdown()
