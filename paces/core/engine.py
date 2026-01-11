"""
Paces Engine - Main orchestration for renewable energy platform.

Coordinates all modules including solar/wind analytics, forecasting,
battery management, grid integration, and AI-driven insights.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional
from uuid import uuid4

from loguru import logger

from paces.core.config import PacesConfig, load_paces_config
from paces.core.types import (
    AlertSeverity,
    Portfolio,
    SolarFarm,
    WindFarm,
    BatterySystem,
    GridConnection,
    PowerForecast,
    WeatherData,
    EnergyReading,
    CarbonMetrics,
    FinancialMetrics,
    MaintenanceEvent,
    Defect,
)


class PacesEngine:
    """
    Main orchestration engine for Paces renewable energy platform.

    Coordinates:
    - Asset management (solar, wind, battery)
    - AI-powered defect detection and analysis
    - Energy production forecasting
    - Weather integration
    - Grid interaction
    - Predictive maintenance
    - Financial and carbon tracking
    - Real-time monitoring and alerts
    """

    def __init__(self, config: Optional[PacesConfig] = None):
        self.config = config or load_paces_config()
        self.config.ensure_directories()

        # Module references (lazy loaded)
        self._solar_analyzer = None
        self._wind_analyzer = None
        self._battery_manager = None
        self._forecast_engine = None
        self._grid_manager = None
        self._maintenance_engine = None
        self._carbon_tracker = None
        self._financial_analyzer = None

        # Portfolio
        self._portfolio: Optional[Portfolio] = None

        # State
        self._running = False
        self._initialized = False

        # Callbacks
        self._on_alert: Optional[Callable] = None
        self._on_forecast_update: Optional[Callable] = None
        self._on_defect_detected: Optional[Callable] = None

        # Metrics
        self._stats = {
            "total_inspections": 0,
            "defects_detected": 0,
            "forecasts_generated": 0,
            "alerts_sent": 0,
            "energy_monitored_mwh": 0.0,
        }

        logger.info("Paces Engine initialized")

    # =========================================================================
    # Initialization
    # =========================================================================

    async def initialize(self) -> bool:
        """Initialize all engine components."""
        logger.info("Initializing Paces Engine components...")

        try:
            # Initialize modules based on config
            init_tasks = []

            if self.config.solar.enabled:
                init_tasks.append(self._init_solar_analyzer())

            if self.config.wind.enabled:
                init_tasks.append(self._init_wind_analyzer())

            if self.config.battery.enabled:
                init_tasks.append(self._init_battery_manager())

            if self.config.forecasting.enabled:
                init_tasks.append(self._init_forecast_engine())

            if self.config.grid.enabled:
                init_tasks.append(self._init_grid_manager())

            if self.config.maintenance.enabled:
                init_tasks.append(self._init_maintenance_engine())

            if self.config.carbon.enabled:
                init_tasks.append(self._init_carbon_tracker())

            if self.config.financial.enabled:
                init_tasks.append(self._init_financial_analyzer())

            await asyncio.gather(*init_tasks)

            self._initialized = True
            logger.info("Paces Engine initialization complete")
            return True

        except Exception as e:
            logger.error(f"Engine initialization failed: {e}")
            return False

    async def _init_solar_analyzer(self) -> None:
        """Initialize solar analytics module."""
        from paces.solar.analyzer import SolarAnalyzer
        self._solar_analyzer = SolarAnalyzer(self.config)
        await self._solar_analyzer.initialize()
        logger.info("Solar Analyzer initialized")

    async def _init_wind_analyzer(self) -> None:
        """Initialize wind analytics module."""
        from paces.wind.analyzer import WindAnalyzer
        self._wind_analyzer = WindAnalyzer(self.config)
        await self._wind_analyzer.initialize()
        logger.info("Wind Analyzer initialized")

    async def _init_battery_manager(self) -> None:
        """Initialize battery management module."""
        from paces.battery.manager import BatteryManager
        self._battery_manager = BatteryManager(self.config)
        await self._battery_manager.initialize()
        logger.info("Battery Manager initialized")

    async def _init_forecast_engine(self) -> None:
        """Initialize forecasting engine."""
        from paces.forecasting.engine import ForecastEngine
        self._forecast_engine = ForecastEngine(self.config)
        await self._forecast_engine.initialize()
        logger.info("Forecast Engine initialized")

    async def _init_grid_manager(self) -> None:
        """Initialize grid integration module."""
        from paces.grid.manager import GridManager
        self._grid_manager = GridManager(self.config)
        await self._grid_manager.initialize()
        logger.info("Grid Manager initialized")

    async def _init_maintenance_engine(self) -> None:
        """Initialize predictive maintenance engine."""
        from paces.maintenance.engine import MaintenanceEngine
        self._maintenance_engine = MaintenanceEngine(self.config)
        await self._maintenance_engine.initialize()
        logger.info("Maintenance Engine initialized")

    async def _init_carbon_tracker(self) -> None:
        """Initialize carbon tracking module."""
        from paces.carbon.tracker import CarbonTracker
        self._carbon_tracker = CarbonTracker(self.config)
        await self._carbon_tracker.initialize()
        logger.info("Carbon Tracker initialized")

    async def _init_financial_analyzer(self) -> None:
        """Initialize financial analytics module."""
        from paces.financial.analyzer import FinancialAnalyzer
        self._financial_analyzer = FinancialAnalyzer(self.config)
        await self._financial_analyzer.initialize()
        logger.info("Financial Analyzer initialized")

    # =========================================================================
    # Portfolio Management
    # =========================================================================

    def load_portfolio(self, portfolio: Portfolio) -> None:
        """Load a renewable energy portfolio."""
        self._portfolio = portfolio
        logger.info(f"Portfolio loaded: {portfolio.name}")
        logger.info(f"  Solar capacity: {portfolio.solar_capacity_mw:.2f} MW")
        logger.info(f"  Wind capacity: {portfolio.wind_capacity_mw:.2f} MW")
        logger.info(f"  Storage: {portfolio.storage_capacity_mwh:.2f} MWh")

    def get_portfolio(self) -> Optional[Portfolio]:
        """Get current portfolio."""
        return self._portfolio

    def get_portfolio_summary(self) -> dict:
        """Get portfolio summary."""
        if not self._portfolio:
            return {}
        return self._portfolio.get_summary()

    # =========================================================================
    # Solar Operations
    # =========================================================================

    async def analyze_solar_farm(
        self,
        farm: SolarFarm,
        thermal_images: list = None,
        rgb_images: list = None,
    ) -> dict:
        """
        Comprehensive solar farm analysis.

        Includes:
        - Panel defect detection
        - Hotspot identification
        - Soiling analysis
        - Performance assessment
        - AI-generated recommendations
        """
        if not self._solar_analyzer:
            raise RuntimeError("Solar analyzer not initialized")

        result = await self._solar_analyzer.analyze_farm(
            farm,
            thermal_images=thermal_images,
            rgb_images=rgb_images,
        )

        self._stats["total_inspections"] += 1
        self._stats["defects_detected"] += len(result.get("defects", []))

        # Trigger alerts for critical defects
        for defect in result.get("defects", []):
            if defect.severity.value >= AlertSeverity.HIGH.value:
                await self._send_alert(defect)

        return result

    async def get_solar_performance(
        self,
        farm_id: str,
        start_time: datetime = None,
        end_time: datetime = None,
    ) -> dict:
        """Get solar farm performance metrics."""
        if not self._solar_analyzer:
            raise RuntimeError("Solar analyzer not initialized")

        return await self._solar_analyzer.get_performance(
            farm_id,
            start_time or datetime.now() - timedelta(days=1),
            end_time or datetime.now(),
        )

    # =========================================================================
    # Wind Operations
    # =========================================================================

    async def analyze_wind_turbine(
        self,
        turbine,
        blade_images: list = None,
        vibration_data: list = None,
    ) -> dict:
        """
        Comprehensive wind turbine analysis.

        Includes:
        - Blade defect detection
        - Vibration analysis
        - Yaw/pitch assessment
        - Performance evaluation
        """
        if not self._wind_analyzer:
            raise RuntimeError("Wind analyzer not initialized")

        return await self._wind_analyzer.analyze_turbine(
            turbine,
            blade_images=blade_images,
            vibration_data=vibration_data,
        )

    async def get_wind_performance(
        self,
        farm_id: str,
        start_time: datetime = None,
        end_time: datetime = None,
    ) -> dict:
        """Get wind farm performance metrics."""
        if not self._wind_analyzer:
            raise RuntimeError("Wind analyzer not initialized")

        return await self._wind_analyzer.get_performance(
            farm_id,
            start_time or datetime.now() - timedelta(days=1),
            end_time or datetime.now(),
        )

    # =========================================================================
    # Battery Operations
    # =========================================================================

    async def get_battery_status(self, system_id: str) -> dict:
        """Get battery system status."""
        if not self._battery_manager:
            raise RuntimeError("Battery manager not initialized")

        return await self._battery_manager.get_status(system_id)

    async def optimize_battery_dispatch(
        self,
        system_id: str,
        horizon_hours: int = 24,
    ) -> dict:
        """Optimize battery dispatch schedule."""
        if not self._battery_manager:
            raise RuntimeError("Battery manager not initialized")

        # Get forecasts for optimization
        if self._forecast_engine:
            price_forecast = await self._forecast_engine.forecast_prices(
                hours=horizon_hours
            )
            load_forecast = await self._forecast_engine.forecast_load(
                hours=horizon_hours
            )
        else:
            price_forecast = None
            load_forecast = None

        return await self._battery_manager.optimize_dispatch(
            system_id,
            price_forecast=price_forecast,
            load_forecast=load_forecast,
            horizon_hours=horizon_hours,
        )

    # =========================================================================
    # Forecasting
    # =========================================================================

    async def forecast_solar_production(
        self,
        farm_id: str,
        hours: int = 48,
    ) -> PowerForecast:
        """Forecast solar production."""
        if not self._forecast_engine:
            raise RuntimeError("Forecast engine not initialized")

        forecast = await self._forecast_engine.forecast_solar(farm_id, hours)
        self._stats["forecasts_generated"] += 1
        return forecast

    async def forecast_wind_production(
        self,
        farm_id: str,
        hours: int = 48,
    ) -> PowerForecast:
        """Forecast wind production."""
        if not self._forecast_engine:
            raise RuntimeError("Forecast engine not initialized")

        forecast = await self._forecast_engine.forecast_wind(farm_id, hours)
        self._stats["forecasts_generated"] += 1
        return forecast

    async def forecast_portfolio_production(
        self,
        hours: int = 48,
    ) -> dict:
        """Forecast total portfolio production."""
        if not self._forecast_engine or not self._portfolio:
            raise RuntimeError("Forecast engine or portfolio not available")

        solar_forecasts = []
        for farm in self._portfolio.solar_farms:
            forecast = await self._forecast_engine.forecast_solar(farm.id, hours)
            solar_forecasts.append(forecast)

        wind_forecasts = []
        for farm in self._portfolio.wind_farms:
            forecast = await self._forecast_engine.forecast_wind(farm.id, hours)
            wind_forecasts.append(forecast)

        return {
            "solar_forecasts": solar_forecasts,
            "wind_forecasts": wind_forecasts,
            "total_forecast": self._aggregate_forecasts(
                solar_forecasts + wind_forecasts
            ),
        }

    def _aggregate_forecasts(self, forecasts: list[PowerForecast]) -> dict:
        """Aggregate multiple forecasts."""
        if not forecasts:
            return {}

        timestamps = forecasts[0].timestamps
        total_power = [0.0] * len(timestamps)

        for forecast in forecasts:
            for i, power in enumerate(forecast.power_kw):
                if i < len(total_power):
                    total_power[i] += power

        return {
            "timestamps": timestamps,
            "power_kw": total_power,
            "total_energy_kwh": sum(total_power),
        }

    async def get_weather_forecast(
        self,
        location,
        days: int = 7,
    ) -> list[WeatherData]:
        """Get weather forecast for a location."""
        if not self._forecast_engine:
            raise RuntimeError("Forecast engine not initialized")

        return await self._forecast_engine.get_weather(location, days)

    # =========================================================================
    # Grid Integration
    # =========================================================================

    async def get_grid_status(self, connection_id: str) -> dict:
        """Get grid connection status."""
        if not self._grid_manager:
            raise RuntimeError("Grid manager not initialized")

        return await self._grid_manager.get_status(connection_id)

    async def set_power_setpoint(
        self,
        connection_id: str,
        power_mw: float,
    ) -> bool:
        """Set power export/import setpoint."""
        if not self._grid_manager:
            raise RuntimeError("Grid manager not initialized")

        return await self._grid_manager.set_power_setpoint(connection_id, power_mw)

    async def respond_to_curtailment(
        self,
        connection_id: str,
        curtailment_mw: float,
    ) -> bool:
        """Respond to grid curtailment signal."""
        if not self._grid_manager:
            raise RuntimeError("Grid manager not initialized")

        return await self._grid_manager.handle_curtailment(
            connection_id,
            curtailment_mw,
        )

    # =========================================================================
    # Predictive Maintenance
    # =========================================================================

    async def predict_failures(
        self,
        asset_id: str,
        horizon_days: int = 30,
    ) -> list[dict]:
        """Predict potential failures for an asset."""
        if not self._maintenance_engine:
            raise RuntimeError("Maintenance engine not initialized")

        return await self._maintenance_engine.predict_failures(
            asset_id,
            horizon_days,
        )

    async def get_maintenance_schedule(
        self,
        asset_ids: list[str] = None,
    ) -> list[MaintenanceEvent]:
        """Get optimized maintenance schedule."""
        if not self._maintenance_engine:
            raise RuntimeError("Maintenance engine not initialized")

        return await self._maintenance_engine.get_schedule(asset_ids)

    async def schedule_maintenance(
        self,
        event: MaintenanceEvent,
    ) -> bool:
        """Schedule a maintenance event."""
        if not self._maintenance_engine:
            raise RuntimeError("Maintenance engine not initialized")

        return await self._maintenance_engine.schedule(event)

    # =========================================================================
    # Carbon & Financial
    # =========================================================================

    async def get_carbon_metrics(
        self,
        asset_id: str = None,
        period: str = "daily",
    ) -> CarbonMetrics:
        """Get carbon metrics."""
        if not self._carbon_tracker:
            raise RuntimeError("Carbon tracker not initialized")

        return await self._carbon_tracker.get_metrics(asset_id, period)

    async def get_financial_metrics(
        self,
        asset_id: str = None,
        period: str = "monthly",
    ) -> FinancialMetrics:
        """Get financial metrics."""
        if not self._financial_analyzer:
            raise RuntimeError("Financial analyzer not initialized")

        return await self._financial_analyzer.get_metrics(asset_id, period)

    async def calculate_roi(
        self,
        asset_id: str,
        years: int = 25,
    ) -> dict:
        """Calculate ROI for an asset."""
        if not self._financial_analyzer:
            raise RuntimeError("Financial analyzer not initialized")

        return await self._financial_analyzer.calculate_roi(asset_id, years)

    # =========================================================================
    # Real-time Monitoring
    # =========================================================================

    async def start_monitoring(self) -> None:
        """Start real-time monitoring loop."""
        if self._running:
            logger.warning("Monitoring already running")
            return

        self._running = True
        logger.info("Starting real-time monitoring")

        asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self) -> None:
        """Stop real-time monitoring."""
        self._running = False
        logger.info("Monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                # Update forecasts periodically
                if self._forecast_engine:
                    await self._update_forecasts()

                # Check for anomalies
                await self._check_anomalies()

                # Update metrics
                await self._update_metrics()

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(10)

    async def _update_forecasts(self) -> None:
        """Update forecasts for all assets."""
        if not self._portfolio:
            return

        for farm in self._portfolio.solar_farms:
            try:
                await self.forecast_solar_production(farm.id)
            except Exception as e:
                logger.warning(f"Solar forecast failed for {farm.id}: {e}")

        for farm in self._portfolio.wind_farms:
            try:
                await self.forecast_wind_production(farm.id)
            except Exception as e:
                logger.warning(f"Wind forecast failed for {farm.id}: {e}")

    async def _check_anomalies(self) -> None:
        """Check for anomalies across all assets."""
        # Implementation would check real-time data for anomalies
        pass

    async def _update_metrics(self) -> None:
        """Update aggregated metrics."""
        # Implementation would update dashboard metrics
        pass

    # =========================================================================
    # Alerts
    # =========================================================================

    def set_alert_callback(self, callback: Callable) -> None:
        """Set callback for alert notifications."""
        self._on_alert = callback

    async def _send_alert(self, defect: Defect) -> None:
        """Send alert for a defect."""
        self._stats["alerts_sent"] += 1

        if self._on_alert:
            await self._on_alert(defect)

        logger.warning(
            f"ALERT: {defect.defect_type.value} detected on {defect.asset_id} "
            f"[{defect.severity.name}]"
        )

    # =========================================================================
    # Statistics & Health
    # =========================================================================

    def get_stats(self) -> dict:
        """Get engine statistics."""
        return {
            **self._stats,
            "running": self._running,
            "initialized": self._initialized,
            "portfolio_loaded": self._portfolio is not None,
        }

    async def health_check(self) -> dict:
        """Perform system health check."""
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "modules": {},
        }

        if self._solar_analyzer:
            health["modules"]["solar"] = "ok"
        if self._wind_analyzer:
            health["modules"]["wind"] = "ok"
        if self._battery_manager:
            health["modules"]["battery"] = "ok"
        if self._forecast_engine:
            health["modules"]["forecasting"] = "ok"
        if self._grid_manager:
            health["modules"]["grid"] = "ok"
        if self._maintenance_engine:
            health["modules"]["maintenance"] = "ok"
        if self._carbon_tracker:
            health["modules"]["carbon"] = "ok"
        if self._financial_analyzer:
            health["modules"]["financial"] = "ok"

        return health

    # =========================================================================
    # Shutdown
    # =========================================================================

    async def shutdown(self) -> None:
        """Shutdown engine and release resources."""
        logger.info("Shutting down Paces Engine...")

        self._running = False

        # Shutdown modules
        if self._solar_analyzer:
            await self._solar_analyzer.shutdown()
        if self._wind_analyzer:
            await self._wind_analyzer.shutdown()
        if self._battery_manager:
            await self._battery_manager.shutdown()
        if self._forecast_engine:
            await self._forecast_engine.shutdown()
        if self._grid_manager:
            await self._grid_manager.shutdown()
        if self._maintenance_engine:
            await self._maintenance_engine.shutdown()

        logger.info("Paces Engine shutdown complete")
