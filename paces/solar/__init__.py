"""Solar farm analytics module."""

from paces.solar.analyzer import SolarAnalyzer
from paces.solar.defect_detector import SolarDefectDetector
from paces.solar.performance import SolarPerformanceAnalyzer
from paces.solar.thermal import SolarThermalAnalyzer

__all__ = [
    "SolarAnalyzer",
    "SolarDefectDetector",
    "SolarPerformanceAnalyzer",
    "SolarThermalAnalyzer",
]
