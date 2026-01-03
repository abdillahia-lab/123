"""
BAHB - Building And Hardware Baseline
Autonomous Drone Inspection System for Data Centers & Substations

Powered by DJI Manifold 3 + Matrice 400 + H30T
"""

__version__ = "1.0.0"
__author__ = "BAHB Team"
__license__ = "Proprietary"

from bahb.core.config import Config
from bahb.core.engine import InspectionEngine

__all__ = ["Config", "InspectionEngine", "__version__"]
