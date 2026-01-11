"""
TerraJinki - The Spirit of Earth Energy

AI-powered renewable energy site intelligence platform that sees what others can't.

Features:
- Multi-Agent AI Orchestration with human-in-the-loop decision gates
- Graph Neural Networks for real-time grid topology analysis
- Satellite Deep Learning for automated land classification
- LLM-Powered Document Intelligence with RAG for zoning ordinance parsing
- Physics-Guided ML for global solar resource prediction
- Exceptional UX with AI copilot and real-time collaboration

Copyright 2026 TerraJinki. All rights reserved.
"""

__version__ = "1.0.0"
__author__ = "TerraJinki AI Team"

from terrajinki.core.engine import TerraJinkiEngine
from terrajinki.core.types import (
    Parcel,
    Project,
    SiteAnalysis,
    SiteScore,
    ApprovalGate,
    HumanDecision,
)

__all__ = [
    "TerraJinkiEngine",
    "Parcel",
    "Project",
    "SiteAnalysis",
    "SiteScore",
    "ApprovalGate",
    "HumanDecision",
]
