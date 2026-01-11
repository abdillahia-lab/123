"""
Paces - AI-Powered Renewable Energy Site Development Platform

A superior site prospecting, permitting analysis, and project development
platform for solar, wind, and energy storage projects.
"""

__version__ = "2.0.0"
__author__ = "Paces AI"

from paces.core.types import (
    Parcel,
    Project,
    ProjectStatus,
    ProjectType,
    PermitStatus,
    GridConnection,
    EnvironmentalConstraint,
    SiteScore,
    FeasibilityReport,
)
from paces.core.config import PacesConfig, load_config
from paces.core.engine import PacesEngine

__all__ = [
    "__version__",
    "Parcel",
    "Project",
    "ProjectStatus",
    "ProjectType",
    "PermitStatus",
    "GridConnection",
    "EnvironmentalConstraint",
    "SiteScore",
    "FeasibilityReport",
    "PacesConfig",
    "load_config",
    "PacesEngine",
]
