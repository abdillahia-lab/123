"""
Paces - State-of-the-Art Renewable Energy Management Platform

A comprehensive AI-powered platform for renewable energy asset management,
combining drone inspection, predictive analytics, and portfolio optimization.

Key Features:
- Solar Farm Analytics & Defect Detection
- Wind Turbine Inspection & Performance Monitoring
- Battery Energy Storage System (BESS) Management
- AI-Powered Energy Forecasting with Weather Integration
- Grid Integration & Power Flow Analysis
- Renewable Portfolio Optimization
- Carbon Footprint Tracking & ESG Reporting
- Predictive Maintenance for Renewable Assets
- Financial Analytics & ROI Calculations

AI Models:
- YOLOv12: Ultra-fast defect detection
- RF-DETR: Precision segmentation
- SAM3 Nano: Mask generation
- Qwen2.5-VL: Visual language analysis
- Temporal Fusion Transformer: Energy forecasting
- GraphCast/Pangu-Weather: Weather prediction integration
"""

__version__ = "1.0.0"
__author__ = "Paces Team"
__license__ = "Proprietary"

from paces.core.types import (
    AssetType,
    EnergySource,
    MaintenanceStatus,
    AlertSeverity,
    WeatherCondition,
)
from paces.core.config import PacesConfig, load_paces_config
from paces.core.engine import PacesEngine

__all__ = [
    "__version__",
    "AssetType",
    "EnergySource",
    "MaintenanceStatus",
    "AlertSeverity",
    "WeatherCondition",
    "PacesConfig",
    "load_paces_config",
    "PacesEngine",
]
