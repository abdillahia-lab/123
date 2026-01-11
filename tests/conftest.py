"""
TerraJinki Test Configuration

Shared fixtures and configuration for all tests.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import Optional

import sys
sys.path.insert(0, '/home/user/123')

from terrajinki.core.types import (
    Parcel, GeoPoint, GeoPolygon, ZoningType, SolarPermission,
    ProjectType, SiteScore, SiteAnalysis, AgentResult, SwarmResult,
    AgentStatus, Jurisdiction, GridAnalysis, EnvironmentalScreening,
    GridViability, EnvironmentalRisk, ApprovalGate, ApprovalLevel
)
from terrajinki.core.config import (
    TerraJinkiConfig, LLMConfig, AgentConfig, ScoringConfig,
    Environment, get_config, set_config
)


# =============================================================================
# FIXTURES: Geographic Data
# =============================================================================

@pytest.fixture
def sample_geo_point():
    """Sample geographic point in Ohio."""
    return GeoPoint(latitude=40.0, longitude=-82.5, elevation_m=300.0)


@pytest.fixture
def sample_geo_polygon():
    """Sample polygon representing a parcel."""
    vertices = [
        GeoPoint(latitude=40.0, longitude=-82.5),
        GeoPoint(latitude=40.01, longitude=-82.5),
        GeoPoint(latitude=40.01, longitude=-82.49),
        GeoPoint(latitude=40.0, longitude=-82.49),
    ]
    return GeoPolygon(vertices=vertices)


# =============================================================================
# FIXTURES: Parcel Data
# =============================================================================

@pytest.fixture
def sample_parcel(sample_geo_point, sample_geo_polygon):
    """Sample parcel for testing."""
    return Parcel(
        id="test-parcel-001",
        apn="123-456-789",
        state="OH",
        county="Franklin",
        municipality="Columbus",
        address="1234 Solar Farm Rd",
        centroid=sample_geo_point,
        boundary=sample_geo_polygon,
        acreage=150.0,
        slope_avg_pct=2.5,
        zoning_type=ZoningType.AGRICULTURAL,
        solar_permission=SolarPermission.CONDITIONAL_USE,
        owner_name="Test Owner LLC",
        assessed_value=500000.0,
        road_access=True,
        nearest_substation_mi=2.5,
    )


@pytest.fixture
def small_parcel():
    """Small parcel (under minimum for utility solar)."""
    return Parcel(
        id="test-parcel-small",
        acreage=5.0,
        state="OH",
        county="Franklin",
        zoning_type=ZoningType.RESIDENTIAL,
        solar_permission=SolarPermission.PROHIBITED,
    )


@pytest.fixture
def excellent_parcel(sample_geo_point):
    """Excellent parcel with ideal conditions."""
    return Parcel(
        id="test-parcel-excellent",
        apn="999-888-777",
        state="TX",
        county="Travis",
        centroid=sample_geo_point,
        acreage=500.0,
        slope_avg_pct=1.0,
        zoning_type=ZoningType.AGRICULTURAL,
        solar_permission=SolarPermission.BY_RIGHT,
        road_access=True,
        nearest_substation_mi=0.5,
    )


# =============================================================================
# FIXTURES: Configuration
# =============================================================================

@pytest.fixture
def test_config():
    """Test configuration with mock API keys."""
    config = TerraJinkiConfig(
        environment=Environment.DEVELOPMENT,
        llm=LLMConfig(
            anthropic_api_key="test-key-123",
            max_cost_per_analysis=10.0,
        ),
        agents=AgentConfig(
            agent_timeout_seconds=30.0,
            fatal_flaw_score_threshold=30.0,
            high_value_score_threshold=90.0,
        ),
        scoring=ScoringConfig(),
    )
    return config


@pytest.fixture
def production_config():
    """Production configuration for validation testing."""
    return TerraJinkiConfig(
        environment=Environment.PRODUCTION,
        llm=LLMConfig(anthropic_api_key="prod-key"),
    )


# =============================================================================
# FIXTURES: Agent Results
# =============================================================================

@pytest.fixture
def sample_agent_result():
    """Sample successful agent result."""
    return AgentResult(
        agent_id="test-agent-001",
        agent_type="permitting_analyzer",
        status=AgentStatus.COMPLETED,
        success=True,
        output={"key": "value"},
        score=75.0,
        confidence=0.85,
        model_used="claude-sonnet-4-20250514",
        tokens_input=1000,
        tokens_output=500,
    )


@pytest.fixture
def sample_swarm_result(sample_agent_result):
    """Sample swarm result with multiple agent results."""
    return SwarmResult(
        swarm_id="test-swarm-001",
        swarm_type="permitting",
        status=AgentStatus.COMPLETED,
        agent_results=[sample_agent_result],
        overall_score=75.0,
        confidence=0.85,
        key_findings=["Zoning allows solar by-right"],
        risks=["Setback requirements may limit capacity"],
        recommendations=["Proceed with conditional use permit"],
    )


@pytest.fixture
def sample_site_score():
    """Sample site score."""
    score = SiteScore(
        parcel_id="test-parcel-001",
        permitting_score=80.0,
        grid_score=75.0,
        environmental_score=85.0,
        land_score=70.0,
        financial_score=65.0,
    )
    score.calculate_overall()
    return score


@pytest.fixture
def sample_site_analysis(sample_parcel, sample_site_score):
    """Sample complete site analysis."""
    return SiteAnalysis(
        id="test-analysis-001",
        parcel_id=sample_parcel.id,
        project_type=ProjectType.UTILITY_SOLAR,
        score=sample_site_score,
        proceed_recommendation="proceed_with_caution",
        recommended_next_steps=["Apply for CUP", "Order interconnection study"],
    )


# =============================================================================
# FIXTURES: Mock LLM Client
# =============================================================================

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing without API calls."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Test LLM response")]
    mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)
    mock_client.messages.create = MagicMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def mock_async_llm():
    """Async mock for LLM calls."""
    async def mock_call(*args, **kwargs):
        return {
            "response": "Mock analysis complete",
            "score": 75.0,
            "findings": ["Finding 1", "Finding 2"],
        }
    return AsyncMock(side_effect=mock_call)


# =============================================================================
# FIXTURES: Context
# =============================================================================

@pytest.fixture
def agent_context(test_config):
    """Agent context for testing."""
    from terrajinki.agents.base import AgentContext
    return AgentContext(config=test_config)


# =============================================================================
# ASYNC HELPERS
# =============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# MOCK DATA SOURCES
# =============================================================================

@pytest.fixture
def mock_parcel_data():
    """Mock parcel data from external API."""
    return {
        "apn": "123-456-789",
        "state": "OH",
        "county": "Franklin",
        "owner": "Test Owner",
        "acreage": 150.0,
        "zoning": "AG",
        "coordinates": [-82.5, 40.0],
    }


@pytest.fixture
def mock_grid_data():
    """Mock grid data from EIA."""
    return {
        "substation": {
            "name": "Franklin Sub",
            "voltage_kv": 138.0,
            "capacity_mw": 200.0,
            "available_mw": 50.0,
        },
        "distance_miles": 2.5,
        "queue_projects": 3,
    }


@pytest.fixture
def mock_environmental_data():
    """Mock environmental screening data."""
    return {
        "wetlands": {"present": False},
        "flood_zone": "X",
        "endangered_species": [],
        "prime_farmland": True,
    }
