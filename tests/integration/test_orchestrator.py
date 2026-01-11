"""
TerraJinki Orchestrator Integration Tests

Tests for the multi-agent orchestrator and swarm coordination.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import json

import sys
sys.path.insert(0, '/home/user/123')

from terrajinki.agents.orchestrator import OrchestratorAgent, AnalysisRequest
from terrajinki.agents.base import AgentContext, LLMClient
from terrajinki.core.types import (
    Parcel, GeoPoint, ZoningType, SolarPermission, ProjectType,
    SiteAnalysis, SiteScore, AgentStatus, SwarmResult
)
from terrajinki.core.config import TerraJinkiConfig, LLMConfig, AgentConfig


@pytest.fixture
def mock_llm_response():
    """Create mock LLM response."""
    return {
        "content": json.dumps({
            "analysis": "Mock analysis",
            "score": 75.0,
            "confidence": 0.85,
            "findings": ["Finding 1", "Finding 2"],
            "risks": ["Risk 1"],
            "recommendations": ["Recommendation 1"],
            "requires_review": False,
            "swarms_to_execute": ["permitting", "grid", "environmental", "land"],
            "execution_order": "parallel",
            "priority_factors": ["grid_proximity", "zoning"],
        }),
        "input_tokens": 100,
        "output_tokens": 50,
        "model": "claude-sonnet-4-20250514_simulated",
    }


@pytest.fixture
def mock_swarm_result():
    """Create mock swarm result."""
    return SwarmResult(
        swarm_id="test-swarm",
        swarm_type="permitting",
        status=AgentStatus.COMPLETED,
        overall_score=75.0,
        confidence=0.85,
        key_findings=["Test finding"],
        risks=["Test risk"],
        recommendations=["Test recommendation"],
    )


class TestAnalysisRequest:
    """Tests for AnalysisRequest dataclass."""

    def test_creation(self, sample_parcel):
        """Test AnalysisRequest creation."""
        request = AnalysisRequest(
            parcel=sample_parcel,
            project_type=ProjectType.UTILITY_SOLAR,
            priority="normal",
        )

        assert request.parcel == sample_parcel
        assert request.project_type == ProjectType.UTILITY_SOLAR
        assert request.priority == "normal"

    def test_default_values(self, sample_parcel):
        """Test AnalysisRequest defaults."""
        request = AnalysisRequest(parcel=sample_parcel)

        assert request.project_type == ProjectType.UTILITY_SOLAR
        assert request.include_financial is True
        assert request.target_capacity_mw == 0.0


class TestOrchestrator:
    """Tests for OrchestratorAgent class."""

    @pytest.fixture
    def orchestrator(self, agent_context, mock_llm_response):
        """Create orchestrator instance with mocked LLM."""
        orch = OrchestratorAgent(context=agent_context)
        # Mock the LLM to avoid real API calls
        orch.llm._simulate_response = MagicMock(return_value=mock_llm_response)
        return orch

    def test_creation(self, orchestrator):
        """Test OrchestratorAgent creation."""
        assert orchestrator.name == "orchestrator"
        assert len(orchestrator._swarms) == 4  # permitting, grid, environmental, land

    def test_swarms_initialized(self, orchestrator):
        """Test all swarms are properly initialized."""
        assert "permitting" in orchestrator._swarms
        assert "grid" in orchestrator._swarms
        assert "environmental" in orchestrator._swarms
        assert "land" in orchestrator._swarms

    @pytest.mark.asyncio
    async def test_execute_returns_site_analysis(self, agent_context, sample_parcel, mock_llm_response):
        """Test execute returns SiteAnalysis."""
        orchestrator = OrchestratorAgent(context=agent_context)

        # Mock LLM.complete to return simulated response
        async def mock_complete(*args, **kwargs):
            return mock_llm_response
        orchestrator.llm.complete = mock_complete

        # Mock swarm execution
        mock_swarm_result = SwarmResult(overall_score=75.0, swarm_type="test")
        for swarm in orchestrator._swarms.values():
            async def mock_execute(*args, **kwargs):
                return mock_swarm_result
            swarm.execute = mock_execute

        request = AnalysisRequest(parcel=sample_parcel)
        analysis = await orchestrator.execute(request)

        assert isinstance(analysis, SiteAnalysis)
        assert analysis.parcel_id == sample_parcel.id

    @pytest.mark.asyncio
    async def test_score_calculation(self, agent_context, sample_parcel, mock_llm_response):
        """Test overall score calculation from swarm results."""
        orchestrator = OrchestratorAgent(context=agent_context)

        async def mock_complete(*args, **kwargs):
            return mock_llm_response
        orchestrator.llm.complete = mock_complete

        # Mock swarms with specific scores
        for name, swarm in orchestrator._swarms.items():
            result = SwarmResult(overall_score=80.0, swarm_type=name)
            async def make_mock(r):
                async def mock_execute(*args, **kwargs):
                    return r
                return mock_execute
            swarm.execute = await make_mock(result)

        request = AnalysisRequest(parcel=sample_parcel)
        analysis = await orchestrator.execute(request)

        assert analysis.score is not None
        assert analysis.score.overall_score > 0


class TestOrchestratorMockedSwarms:
    """Tests with fully mocked swarm execution."""

    @pytest.fixture
    def orchestrator(self, agent_context, mock_llm_response):
        """Create orchestrator with mocked LLM and swarms."""
        orch = OrchestratorAgent(context=agent_context)

        async def mock_complete(*args, **kwargs):
            return mock_llm_response
        orch.llm.complete = mock_complete

        return orch

    @pytest.mark.asyncio
    async def test_recommendation_proceed(self, orchestrator, sample_parcel, mock_llm_response):
        """Test proceed recommendation for high scores."""
        # Mock swarms with high scores
        for name, swarm in orchestrator._swarms.items():
            result = SwarmResult(overall_score=90.0, swarm_type=name)
            async def make_mock(r):
                async def mock_execute(*args, **kwargs):
                    return r
                return mock_execute
            swarm.execute = await make_mock(result)

        request = AnalysisRequest(parcel=sample_parcel)
        analysis = await orchestrator.execute(request)

        assert "proceed" in analysis.proceed_recommendation.lower()

    @pytest.mark.asyncio
    async def test_recommendation_caution(self, orchestrator, sample_parcel, mock_llm_response):
        """Test caution recommendation for medium scores."""
        for name, swarm in orchestrator._swarms.items():
            result = SwarmResult(overall_score=60.0, swarm_type=name)
            async def make_mock(r):
                async def mock_execute(*args, **kwargs):
                    return r
                return mock_execute
            swarm.execute = await make_mock(result)

        request = AnalysisRequest(parcel=sample_parcel)
        analysis = await orchestrator.execute(request)

        assert "caution" in analysis.proceed_recommendation.lower()

    @pytest.mark.asyncio
    async def test_recommendation_low_score_triggers_review(self, orchestrator, sample_parcel, mock_llm_response):
        """Test low scores trigger human review requirement."""
        for name, swarm in orchestrator._swarms.items():
            result = SwarmResult(overall_score=20.0, swarm_type=name)
            async def make_mock(r):
                async def mock_execute(*args, **kwargs):
                    return r
                return mock_execute
            swarm.execute = await make_mock(result)

        request = AnalysisRequest(parcel=sample_parcel)
        analysis = await orchestrator.execute(request)

        # Low scores should require human review and show fatal viability
        assert analysis.requires_human_review is True
        assert analysis.score.viability == "fatal"
        assert analysis.score.overall_score < 30


class TestSwarmExecutionMocked:
    """Tests for individual swarm execution with mocked LLM."""

    @pytest.fixture
    def orchestrator(self, agent_context, mock_llm_response):
        """Create orchestrator."""
        orch = OrchestratorAgent(context=agent_context)

        async def mock_complete(*args, **kwargs):
            return mock_llm_response
        orch.llm.complete = mock_complete

        # Also mock swarm LLM calls
        for swarm in orch._swarms.values():
            swarm.llm.complete = mock_complete

        return orch

    @pytest.mark.asyncio
    async def test_permitting_swarm_execution(self, orchestrator, sample_parcel, mock_llm_response):
        """Test permitting swarm runs successfully."""
        swarm = orchestrator._swarms["permitting"]
        swarm.llm.complete = AsyncMock(return_value=mock_llm_response)

        result = await swarm.execute({"parcel": sample_parcel})

        assert isinstance(result, SwarmResult)
        assert result.swarm_type == "permitting"

    @pytest.mark.asyncio
    async def test_grid_swarm_execution(self, orchestrator, sample_parcel, mock_llm_response):
        """Test grid swarm runs successfully."""
        swarm = orchestrator._swarms["grid"]
        swarm.llm.complete = AsyncMock(return_value=mock_llm_response)

        result = await swarm.execute({"parcel": sample_parcel})

        assert isinstance(result, SwarmResult)
        assert result.swarm_type == "grid"

    @pytest.mark.asyncio
    async def test_environmental_swarm_execution(self, orchestrator, sample_parcel, mock_llm_response):
        """Test environmental swarm runs successfully."""
        swarm = orchestrator._swarms["environmental"]
        swarm.llm.complete = AsyncMock(return_value=mock_llm_response)

        result = await swarm.execute({"parcel": sample_parcel})

        assert isinstance(result, SwarmResult)
        assert result.swarm_type == "environmental"

    @pytest.mark.asyncio
    async def test_land_swarm_execution(self, orchestrator, sample_parcel, mock_llm_response):
        """Test land swarm runs successfully."""
        swarm = orchestrator._swarms["land"]
        swarm.llm.complete = AsyncMock(return_value=mock_llm_response)

        result = await swarm.execute({"parcel": sample_parcel})

        assert isinstance(result, SwarmResult)
        assert result.swarm_type == "land"


class TestParallelExecution:
    """Tests for parallel swarm execution."""

    @pytest.fixture
    def orchestrator(self, agent_context, mock_llm_response):
        """Create orchestrator."""
        orch = OrchestratorAgent(context=agent_context)

        async def mock_complete(*args, **kwargs):
            return mock_llm_response
        orch.llm.complete = mock_complete

        return orch

    @pytest.mark.asyncio
    async def test_swarms_complete_analysis(self, orchestrator, sample_parcel, mock_llm_response):
        """Test swarms complete analysis flow."""
        # Mock all swarm executions
        for name, swarm in orchestrator._swarms.items():
            result = SwarmResult(overall_score=75.0, swarm_type=name)
            async def make_mock(r):
                async def mock_execute(*args, **kwargs):
                    await asyncio.sleep(0.01)  # Small delay
                    return r
                return mock_execute
            swarm.execute = await make_mock(result)

        request = AnalysisRequest(parcel=sample_parcel)

        import time
        start = time.time()
        analysis = await orchestrator.execute(request)
        elapsed = time.time() - start

        assert analysis is not None
        assert isinstance(analysis, SiteAnalysis)
        # Should complete quickly (under 5 seconds with mocks)
        assert elapsed < 5
