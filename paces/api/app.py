"""
Paces REST API - FastAPI-based API for renewable energy platform.

Provides endpoints for:
- Portfolio management
- Asset monitoring
- Forecasting
- Analytics
- Reports
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from paces.core.config import PacesConfig, load_paces_config
from paces.core.engine import PacesEngine
from paces.core.types import GeoLocation, Portfolio


# =============================================================================
# Request/Response Models
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    modules: dict


class PortfolioSummary(BaseModel):
    id: str
    name: str
    solar_capacity_mw: float
    wind_capacity_mw: float
    storage_capacity_mwh: float
    current_generation_mw: float
    total_assets: int


class ForecastRequest(BaseModel):
    asset_id: str
    hours: int = 48
    include_uncertainty: bool = True


class ForecastResponse(BaseModel):
    asset_id: str
    generated_at: str
    horizon_hours: int
    timestamps: list[str]
    power_kw: list[float]
    total_energy_kwh: float


class InspectionRequest(BaseModel):
    asset_id: str
    asset_type: str


class MetricsResponse(BaseModel):
    timestamp: str
    metrics: dict


# =============================================================================
# API Application
# =============================================================================

def create_app(config: PacesConfig = None) -> FastAPI:
    """Create FastAPI application."""
    if config is None:
        config = load_paces_config()

    app = FastAPI(
        title="Paces API",
        description="State-of-the-Art Renewable Energy Management Platform",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Engine instance
    engine = PacesEngine(config)

    # ==========================================================================
    # Health & Status
    # ==========================================================================

    @app.get("/api/health", response_model=HealthResponse)
    async def health_check():
        """System health check."""
        health = await engine.health_check()
        return HealthResponse(
            status=health["status"],
            timestamp=health["timestamp"],
            version="1.0.0",
            modules=health.get("modules", {}),
        )

    @app.get("/api/stats")
    async def get_stats():
        """Get engine statistics."""
        return engine.get_stats()

    # ==========================================================================
    # Portfolio
    # ==========================================================================

    @app.get("/api/portfolio", response_model=PortfolioSummary)
    async def get_portfolio():
        """Get portfolio summary."""
        portfolio = engine.get_portfolio()
        if not portfolio:
            raise HTTPException(status_code=404, detail="No portfolio loaded")

        summary = portfolio.get_summary()
        return PortfolioSummary(**summary)

    @app.get("/api/portfolio/assets")
    async def list_assets():
        """List all portfolio assets."""
        portfolio = engine.get_portfolio()
        if not portfolio:
            raise HTTPException(status_code=404, detail="No portfolio loaded")

        assets = []
        for farm in portfolio.solar_farms:
            assets.append({
                "id": farm.id,
                "name": farm.name,
                "type": "solar_farm",
                "capacity_mw": farm.dc_capacity_mw,
                "status": farm.status.value,
            })
        for farm in portfolio.wind_farms:
            assets.append({
                "id": farm.id,
                "name": farm.name,
                "type": "wind_farm",
                "capacity_mw": farm.rated_capacity_kw / 1000,
                "status": farm.status.value,
            })
        for battery in portfolio.battery_systems:
            assets.append({
                "id": battery.id,
                "name": battery.name,
                "type": "battery",
                "capacity_mwh": battery.energy_capacity_mwh,
                "status": battery.status.value,
            })

        return {"assets": assets}

    # ==========================================================================
    # Forecasting
    # ==========================================================================

    @app.post("/api/forecast/solar", response_model=ForecastResponse)
    async def forecast_solar(request: ForecastRequest):
        """Generate solar power forecast."""
        try:
            forecast = await engine.forecast_solar_production(
                farm_id=request.asset_id,
                hours=request.hours,
            )
            return ForecastResponse(
                asset_id=forecast.asset_id,
                generated_at=forecast.generated_at.isoformat(),
                horizon_hours=forecast.horizon_hours,
                timestamps=[t.isoformat() for t in forecast.timestamps],
                power_kw=forecast.power_kw,
                total_energy_kwh=forecast.total_energy_kwh,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/forecast/wind", response_model=ForecastResponse)
    async def forecast_wind(request: ForecastRequest):
        """Generate wind power forecast."""
        try:
            forecast = await engine.forecast_wind_production(
                farm_id=request.asset_id,
                hours=request.hours,
            )
            return ForecastResponse(
                asset_id=forecast.asset_id,
                generated_at=forecast.generated_at.isoformat(),
                horizon_hours=forecast.horizon_hours,
                timestamps=[t.isoformat() for t in forecast.timestamps],
                power_kw=forecast.power_kw,
                total_energy_kwh=forecast.total_energy_kwh,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/forecast/weather")
    async def forecast_weather(
        lat: float = Query(...),
        lon: float = Query(...),
        days: int = Query(default=7),
    ):
        """Get weather forecast."""
        location = GeoLocation(latitude=lat, longitude=lon)
        try:
            weather = await engine.get_weather_forecast(location, days)
            return {
                "location": location.to_dict(),
                "forecast": [w.to_dict() for w in weather],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ==========================================================================
    # Battery
    # ==========================================================================

    @app.get("/api/battery/{system_id}/status")
    async def get_battery_status(system_id: str):
        """Get battery system status."""
        try:
            status = await engine.get_battery_status(system_id)
            return status.__dict__
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/battery/{system_id}/optimize")
    async def optimize_battery(system_id: str, hours: int = 24):
        """Optimize battery dispatch."""
        try:
            schedule = await engine.optimize_battery_dispatch(system_id, hours)
            return schedule.__dict__
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ==========================================================================
    # Grid
    # ==========================================================================

    @app.get("/api/grid/{connection_id}/status")
    async def get_grid_status(connection_id: str):
        """Get grid connection status."""
        try:
            status = await engine.get_grid_status(connection_id)
            return status
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ==========================================================================
    # Maintenance
    # ==========================================================================

    @app.get("/api/maintenance/{asset_id}/predictions")
    async def get_failure_predictions(asset_id: str, days: int = 30):
        """Get failure predictions for an asset."""
        try:
            predictions = await engine.predict_failures(asset_id, days)
            return {"predictions": [p.__dict__ for p in predictions]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/maintenance/schedule")
    async def get_maintenance_schedule():
        """Get maintenance schedule."""
        try:
            schedule = await engine.get_maintenance_schedule()
            return {"events": [e.__dict__ for e in schedule]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ==========================================================================
    # Carbon & Financial
    # ==========================================================================

    @app.get("/api/carbon/metrics")
    async def get_carbon_metrics(
        asset_id: str = None,
        period: str = "daily",
    ):
        """Get carbon metrics."""
        try:
            metrics = await engine.get_carbon_metrics(asset_id, period)
            return metrics.__dict__
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/financial/metrics")
    async def get_financial_metrics(
        asset_id: str = None,
        period: str = "monthly",
    ):
        """Get financial metrics."""
        try:
            metrics = await engine.get_financial_metrics(asset_id, period)
            return metrics.__dict__
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/financial/roi/{asset_id}")
    async def get_roi_analysis(asset_id: str, years: int = 25):
        """Get ROI analysis for an asset."""
        try:
            roi = await engine.calculate_roi(asset_id, years)
            return roi
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ==========================================================================
    # Startup & Shutdown
    # ==========================================================================

    @app.on_event("startup")
    async def startup():
        """Initialize engine on startup."""
        logger.info("Starting Paces API...")
        await engine.initialize()
        logger.info("Paces API started")

    @app.on_event("shutdown")
    async def shutdown():
        """Shutdown engine."""
        logger.info("Shutting down Paces API...")
        await engine.shutdown()
        logger.info("Paces API shutdown complete")

    return app


# For running with uvicorn directly
app = create_app()
