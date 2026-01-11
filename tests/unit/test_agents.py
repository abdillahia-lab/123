"""
TerraJinki Agent Unit Tests

Tests for base agent, context, LLM client, and approval gates.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
sys.path.insert(0, '/home/user/123')

from terrajinki.agents.base import (
    AgentContext, LLMClient, BaseAgent, ToolAgent, CompositeAgent
)
from terrajinki.core.types import (
    AgentResult, AgentStatus, ApprovalGate, ApprovalLevel, SiteScore
)
from terrajinki.core.config import TerraJinkiConfig, LLMConfig, AgentConfig


class TestAgentContext:
    """Tests for AgentContext class."""

    def test_creation_defaults(self):
        """Test AgentContext with default values."""
        ctx = AgentContext()
        assert ctx.request_id is not None
        assert ctx.total_tokens == 0
        assert ctx.total_cost == 0.0

    def test_creation_with_config(self, test_config):
        """Test AgentContext with custom config."""
        ctx = AgentContext(config=test_config)
        assert ctx.config == test_config

    def test_add_tokens_claude_sonnet(self, test_config):
        """Test token cost calculation for Claude Sonnet."""
        ctx = AgentContext(config=test_config)
        cost = ctx.add_tokens(1000, 500, "claude-sonnet-4-20250514")

        assert ctx.total_tokens == 1500
        assert cost > 0
        assert ctx.total_cost == cost

    def test_add_tokens_claude_haiku(self, test_config):
        """Test token cost calculation for Claude Haiku."""
        ctx = AgentContext(config=test_config)
        cost = ctx.add_tokens(1000, 500, "claude-3-5-haiku-20241022")

        # Haiku should be cheaper than Sonnet
        ctx2 = AgentContext(config=test_config)
        sonnet_cost = ctx2.add_tokens(1000, 500, "claude-sonnet-4-20250514")

        assert cost < sonnet_cost

    def test_add_tokens_unknown_model(self, test_config):
        """Test token cost with unknown model uses defaults."""
        ctx = AgentContext(config=test_config)
        cost = ctx.add_tokens(1000, 500, "unknown-model-xyz")

        assert cost > 0
        assert ctx.total_cost == cost

    def test_cache_usage(self):
        """Test cache storage and retrieval."""
        ctx = AgentContext()
        ctx.cache["key1"] = {"value": 123}
        assert ctx.cache["key1"]["value"] == 123

    def test_metadata_storage(self):
        """Test metadata storage."""
        ctx = AgentContext(metadata={"project": "test"})
        assert ctx.metadata["project"] == "test"


class TestLLMClient:
    """Tests for LLMClient class."""

    def test_creation(self, test_config):
        """Test LLMClient creation."""
        client = LLMClient(test_config)
        assert client.config == test_config
        assert client._anthropic_client is None
        assert client._openai_client is None

    @pytest.mark.asyncio
    async def test_simulate_response(self, test_config):
        """Test simulated response when no API key."""
        client = LLMClient(test_config)
        messages = [{"role": "user", "content": "Analyze this parcel"}]

        response = client._simulate_response(messages, "test-model")

        assert "content" in response
        assert "input_tokens" in response
        assert "output_tokens" in response
        assert "_simulated" in response["model"]

    @pytest.mark.asyncio
    async def test_complete_routes_to_anthropic(self, test_config):
        """Test complete routes Claude models to Anthropic."""
        client = LLMClient(test_config)

        with patch.object(client, '_complete_anthropic', new_callable=AsyncMock) as mock:
            mock.return_value = {"content": "test", "input_tokens": 10, "output_tokens": 5, "model": "test"}
            await client.complete(
                messages=[{"role": "user", "content": "test"}],
                model="claude-sonnet-4-20250514"
            )
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_routes_to_openai(self, test_config):
        """Test complete routes GPT models to OpenAI."""
        client = LLMClient(test_config)

        with patch.object(client, '_complete_openai', new_callable=AsyncMock) as mock:
            mock.return_value = {"content": "test", "input_tokens": 10, "output_tokens": 5, "model": "test"}
            await client.complete(
                messages=[{"role": "user", "content": "test"}],
                model="gpt-4o"
            )
            mock.assert_called_once()


class SimpleTestAgent(BaseAgent[dict, dict]):
    """Simple agent for testing."""
    name = "test_agent"
    description = "Test agent for unit tests"

    async def execute(self, input_data: dict) -> dict:
        return {"result": "success", "score": input_data.get("score", 50.0)}


class FailingAgent(BaseAgent[dict, dict]):
    """Agent that always fails."""
    name = "failing_agent"
    description = "Agent that fails"

    async def execute(self, input_data: dict) -> dict:
        raise ValueError("Intentional failure")


class SlowAgent(BaseAgent[dict, dict]):
    """Agent that takes time."""
    name = "slow_agent"
    description = "Slow agent"

    async def execute(self, input_data: dict) -> dict:
        await asyncio.sleep(input_data.get("delay", 0.1))
        return {"result": "completed"}


class TestBaseAgent:
    """Tests for BaseAgent class."""

    @pytest.mark.asyncio
    async def test_run_successful(self, agent_context):
        """Test successful agent run."""
        agent = SimpleTestAgent(context=agent_context)
        result = await agent.run({"score": 75.0})

        assert result.status == AgentStatus.COMPLETED
        assert result.success is True
        assert result.output["result"] == "success"
        assert result.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_run_failure(self, agent_context):
        """Test agent failure handling."""
        agent = FailingAgent(context=agent_context)
        result = await agent.run({})

        assert result.status == AgentStatus.FAILED
        assert result.success is False
        assert "Intentional failure" in result.error_message

    @pytest.mark.asyncio
    async def test_agent_id_unique(self, agent_context):
        """Test each agent gets unique ID."""
        agent1 = SimpleTestAgent(context=agent_context)
        agent2 = SimpleTestAgent(context=agent_context)
        assert agent1.id != agent2.id

    @pytest.mark.asyncio
    async def test_approval_gate_low_score(self, agent_context):
        """Test approval gate triggers on low score."""
        agent = SimpleTestAgent(context=agent_context)
        result = await agent.run({"score": 20.0})

        # Score below threshold should require approval
        assert result.requires_approval is True
        assert "fatal_flaw" in result.approval_reason.lower() or "below threshold" in result.approval_reason.lower()

    @pytest.mark.asyncio
    async def test_approval_gate_high_score(self, agent_context):
        """Test notification on high score."""
        # Modify config for test
        agent_context.config.agents.high_value_score_threshold = 85.0
        agent = SimpleTestAgent(context=agent_context)
        result = await agent.run({"score": 95.0})

        assert result.requires_approval is True
        assert "high" in result.approval_reason.lower()

    @pytest.mark.asyncio
    async def test_approval_gate_normal_score(self, agent_context):
        """Test no approval required for normal score."""
        agent = SimpleTestAgent(context=agent_context)
        result = await agent.run({"score": 60.0})

        assert result.requires_approval is False

    @pytest.mark.asyncio
    async def test_serialize_dict_output(self, agent_context):
        """Test dict output serialization."""
        agent = SimpleTestAgent(context=agent_context)
        output = agent._serialize_output({"key": "value"})
        assert output == {"key": "value"}

    @pytest.mark.asyncio
    async def test_serialize_object_output(self, agent_context):
        """Test object with to_dict serialization."""
        class TestObj:
            def to_dict(self):
                return {"converted": True}

        agent = SimpleTestAgent(context=agent_context)
        output = agent._serialize_output(TestObj())
        assert output == {"converted": True}

    @pytest.mark.asyncio
    async def test_system_prompt(self, agent_context):
        """Test system prompt generation."""
        agent = SimpleTestAgent(context=agent_context)
        prompt = agent._get_system_prompt()

        assert "test_agent" in prompt
        assert "Test agent for unit tests" in prompt
        assert "JSON" in prompt

    @pytest.mark.asyncio
    async def test_call_llm_tracks_usage(self, agent_context):
        """Test LLM call tracks token usage."""
        agent = SimpleTestAgent(context=agent_context)

        # Mock the LLM client
        with patch.object(agent.llm, 'complete', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "content": '{"result": "test"}',
                "input_tokens": 100,
                "output_tokens": 50,
                "model": "claude-sonnet-4-20250514"
            }
            await agent.call_llm("Test prompt")

        assert agent_context.total_tokens == 150

    @pytest.mark.asyncio
    async def test_check_approval_with_site_score(self, agent_context):
        """Test approval check with SiteScore object."""
        agent = SimpleTestAgent(context=agent_context)

        # Create SiteScore with low overall
        site_score = SiteScore(
            permitting_score=20.0,
            grid_score=20.0,
            environmental_score=20.0,
            land_score=20.0,
            financial_score=20.0,
        )
        site_score.calculate_overall()

        result = AgentResult(score=site_score)
        gate = await agent._check_approval_required(result)

        assert gate is not None
        assert gate.level == ApprovalLevel.APPROVE


class TestCompositeAgent:
    """Tests for CompositeAgent class."""

    @pytest.mark.asyncio
    async def test_add_agent(self, agent_context):
        """Test adding sub-agents."""
        class TestComposite(CompositeAgent):
            async def execute(self, input_data):
                return {"count": len(self.sub_agents)}

        composite = TestComposite(context=agent_context)
        composite.add_agent(SimpleTestAgent())
        composite.add_agent(SimpleTestAgent())

        result = await composite.execute({})
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_run_parallel(self, agent_context):
        """Test parallel agent execution."""
        class TestComposite(CompositeAgent):
            async def execute(self, input_data):
                return {}

        composite = TestComposite(context=agent_context)
        agent1 = SlowAgent(context=agent_context)
        agent2 = SlowAgent(context=agent_context)

        start = asyncio.get_event_loop().time()
        results = await composite.run_parallel([
            (agent1, {"delay": 0.1}),
            (agent2, {"delay": 0.1}),
        ])
        elapsed = asyncio.get_event_loop().time() - start

        assert len(results) == 2
        # Parallel should take ~0.1s, not 0.2s
        assert elapsed < 0.2

    @pytest.mark.asyncio
    async def test_run_sequential(self, agent_context):
        """Test sequential agent execution."""
        class TestComposite(CompositeAgent):
            async def execute(self, input_data):
                return {}

        composite = TestComposite(context=agent_context)
        agent1 = SlowAgent(context=agent_context)
        agent2 = SlowAgent(context=agent_context)

        start = asyncio.get_event_loop().time()
        results = await composite.run_sequential([
            (agent1, {"delay": 0.05}),
            (agent2, {"delay": 0.05}),
        ])
        elapsed = asyncio.get_event_loop().time() - start

        assert len(results) == 2
        # Sequential should take ~0.1s
        assert elapsed >= 0.1


class TestToolAgent:
    """Tests for ToolAgent class."""

    @pytest.mark.asyncio
    async def test_call_tool_not_implemented(self, agent_context):
        """Test call_tool raises NotImplementedError."""
        class TestTool(ToolAgent):
            async def execute(self, input_data):
                return await self.call_tool("test_tool")

        agent = TestTool(context=agent_context)
        with pytest.raises(NotImplementedError):
            await agent.execute({})


class TestApprovalGate:
    """Tests for ApprovalGate class."""

    def test_creation(self):
        """Test ApprovalGate creation."""
        gate = ApprovalGate(
            name="test_gate",
            description="Test approval gate",
            level=ApprovalLevel.APPROVE,
            score_threshold=30.0,
        )

        assert gate.name == "test_gate"
        assert gate.level == ApprovalLevel.APPROVE
        assert gate.timeout_hours == 24.0

    def test_different_levels(self):
        """Test different approval levels."""
        autonomous = ApprovalGate(level=ApprovalLevel.AUTONOMOUS)
        notify = ApprovalGate(level=ApprovalLevel.NOTIFY)
        approve = ApprovalGate(level=ApprovalLevel.APPROVE)
        collaborate = ApprovalGate(level=ApprovalLevel.COLLABORATE)

        assert autonomous.level == ApprovalLevel.AUTONOMOUS
        assert notify.level == ApprovalLevel.NOTIFY
        assert approve.level == ApprovalLevel.APPROVE
        assert collaborate.level == ApprovalLevel.COLLABORATE
