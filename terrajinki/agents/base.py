"""
TerraJinki Base Agent

Foundation for all agents with LLM integration, structured output,
and human-in-the-loop support.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    Optional, Dict, List, Any, TypeVar, Generic,
    Callable, Awaitable, Type
)
from uuid import uuid4
import asyncio
import json
import logging
import time
import traceback

from terrajinki.core.types import (
    AgentResult,
    AgentStatus,
    ApprovalGate,
    ApprovalLevel,
    HumanDecision,
)
from terrajinki.core.config import get_config, TerraJinkiConfig

logger = logging.getLogger(__name__)

# Type variable for agent input/output
TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


@dataclass
class AgentContext:
    """
    Execution context shared across agent invocations.

    Provides access to configuration, shared state, and
    human-in-the-loop callbacks.
    """
    config: TerraJinkiConfig = field(default_factory=get_config)

    # Request tracking
    request_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    session_id: str = ""

    # Shared state
    cache: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Callbacks for human-in-the-loop
    on_approval_required: Optional[Callable[[ApprovalGate, Dict[str, Any]], Awaitable[HumanDecision]]] = None
    on_notification: Optional[Callable[[str, str, Dict[str, Any]], Awaitable[None]]] = None
    on_progress: Optional[Callable[[str, float, str], Awaitable[None]]] = None

    # Execution tracking
    start_time: datetime = field(default_factory=datetime.utcnow)
    total_tokens: int = 0
    total_cost: float = 0.0

    def add_tokens(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Track token usage and calculate cost."""
        self.total_tokens += input_tokens + output_tokens

        # Approximate costs (per 1M tokens)
        costs = {
            "claude-opus-4-5-20251101": (15.0, 75.0),  # input, output
            "claude-sonnet-4-20250514": (3.0, 15.0),
            "claude-3-5-haiku-20241022": (0.25, 1.25),
            "gpt-4o": (2.5, 10.0),
            "gpt-4o-mini": (0.15, 0.6),
        }

        input_rate, output_rate = costs.get(model, (5.0, 15.0))
        cost = (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000
        self.total_cost += cost
        return cost


class LLMClient:
    """
    Unified LLM client supporting multiple providers.

    Handles retries, rate limiting, and structured output.
    """

    def __init__(self, config: TerraJinkiConfig):
        self.config = config
        self._anthropic_client = None
        self._openai_client = None

    async def _get_anthropic_client(self):
        """Lazy load Anthropic client."""
        if self._anthropic_client is None:
            try:
                import anthropic
                self._anthropic_client = anthropic.AsyncAnthropic(
                    api_key=self.config.llm.anthropic_api_key
                )
            except ImportError:
                logger.warning("Anthropic SDK not installed")
        return self._anthropic_client

    async def _get_openai_client(self):
        """Lazy load OpenAI client."""
        if self._openai_client is None:
            try:
                import openai
                self._openai_client = openai.AsyncOpenAI(
                    api_key=self.config.llm.openai_api_key
                )
            except ImportError:
                logger.warning("OpenAI SDK not installed")
        return self._openai_client

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        json_mode: bool = False,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Send completion request to LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (defaults to config)
            system: System prompt
            max_tokens: Maximum response tokens
            temperature: Sampling temperature
            json_mode: Request JSON output
            retry_count: Current retry attempt

        Returns:
            Dict with 'content', 'input_tokens', 'output_tokens', 'model'
        """
        if not model:
            model = self.config.llm.anthropic_model_analysis

        # Use Claude by default
        if "claude" in model or "anthropic" in model.lower():
            return await self._complete_anthropic(
                messages, model, system, max_tokens, temperature, json_mode, retry_count
            )
        else:
            return await self._complete_openai(
                messages, model, system, max_tokens, temperature, json_mode, retry_count
            )

    async def _complete_anthropic(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system: str,
        max_tokens: int,
        temperature: float,
        json_mode: bool,
        retry_count: int,
    ) -> Dict[str, Any]:
        """Send request to Anthropic API."""
        client = await self._get_anthropic_client()

        if client is None:
            # Simulation mode when no API key
            return self._simulate_response(messages, model)

        try:
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system if system else "You are a helpful assistant.",
                messages=messages,
            )

            return {
                "content": response.content[0].text,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "model": model,
            }

        except Exception as e:
            if retry_count < self.config.llm.retry_attempts:
                await asyncio.sleep(self.config.llm.retry_delay_seconds * (2 ** retry_count))
                return await self._complete_anthropic(
                    messages, model, system, max_tokens, temperature, json_mode, retry_count + 1
                )
            raise

    async def _complete_openai(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system: str,
        max_tokens: int,
        temperature: float,
        json_mode: bool,
        retry_count: int,
    ) -> Dict[str, Any]:
        """Send request to OpenAI API."""
        client = await self._get_openai_client()

        if client is None:
            return self._simulate_response(messages, model)

        try:
            # Prepend system message
            full_messages = []
            if system:
                full_messages.append({"role": "system", "content": system})
            full_messages.extend(messages)

            kwargs = {
                "model": model,
                "messages": full_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = await client.chat.completions.create(**kwargs)

            return {
                "content": response.choices[0].message.content,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "model": model,
            }

        except Exception as e:
            if retry_count < self.config.llm.retry_attempts:
                await asyncio.sleep(self.config.llm.retry_delay_seconds * (2 ** retry_count))
                return await self._complete_openai(
                    messages, model, system, max_tokens, temperature, json_mode, retry_count + 1
                )
            raise

    def _simulate_response(self, messages: List[Dict[str, str]], model: str) -> Dict[str, Any]:
        """Generate simulated response for development/testing."""
        # Extract what we're being asked about
        last_message = messages[-1]["content"] if messages else ""

        # Generate contextual mock response
        mock_content = json.dumps({
            "analysis": "Simulated analysis result",
            "score": 75.0,
            "confidence": 0.85,
            "findings": ["Finding 1", "Finding 2"],
            "recommendations": ["Recommendation 1"],
            "requires_review": False,
        })

        return {
            "content": mock_content,
            "input_tokens": len(last_message.split()) * 2,
            "output_tokens": len(mock_content.split()) * 2,
            "model": model + "_simulated",
        }


class BaseAgent(ABC, Generic[TInput, TOutput]):
    """
    Abstract base class for all TerraJinki agents.

    Provides:
    - LLM integration with structured output
    - Human-in-the-loop approval gates
    - Execution tracking and metrics
    - Error handling and retries
    """

    # Class-level configuration
    name: str = "base_agent"
    description: str = "Base agent"
    model_tier: str = "analysis"  # orchestrator, analysis, fast

    # Approval configuration
    default_approval_level: ApprovalLevel = ApprovalLevel.AUTONOMOUS

    def __init__(self, context: Optional[AgentContext] = None):
        self.context = context or AgentContext()
        self.llm = LLMClient(self.context.config)
        self.id = str(uuid4())
        self._result: Optional[AgentResult] = None

    @abstractmethod
    async def execute(self, input_data: TInput) -> TOutput:
        """
        Execute the agent's primary task.

        Must be implemented by subclasses.

        Args:
            input_data: Agent-specific input

        Returns:
            Agent-specific output
        """
        pass

    async def run(self, input_data: TInput) -> AgentResult:
        """
        Run the agent with full lifecycle management.

        Handles:
        - Execution timing
        - Error handling
        - Approval gates
        - Result packaging

        Args:
            input_data: Agent-specific input

        Returns:
            Standardized AgentResult
        """
        start_time = time.time()
        result = AgentResult(
            agent_id=self.id,
            agent_type=self.name,
            status=AgentStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        try:
            # Execute the agent
            output = await self.execute(input_data)

            # Package result
            result.status = AgentStatus.COMPLETED
            result.success = True
            result.output = self._serialize_output(output)

            # Extract score if available
            if hasattr(output, "score"):
                result.score = output.score
            elif isinstance(output, dict) and "score" in output:
                result.score = output["score"]

            # Check if human approval needed
            approval_gate = await self._check_approval_required(result)
            if approval_gate:
                result.requires_approval = True
                result.approval_reason = approval_gate.description
                result.approval_gate = approval_gate
                result.status = AgentStatus.AWAITING_APPROVAL

                # Request human decision if callback available
                if self.context.on_approval_required:
                    decision = await self.context.on_approval_required(
                        approval_gate,
                        result.output
                    )
                    if decision:
                        result.output["human_decision"] = {
                            "decision": decision.decision,
                            "reasoning": decision.reasoning,
                            "decided_by": decision.decided_by,
                        }
                        result.status = AgentStatus.COMPLETED

        except asyncio.TimeoutError:
            result.status = AgentStatus.FAILED
            result.success = False
            result.error_message = f"Agent timed out after {self.context.config.agents.agent_timeout_seconds}s"

        except Exception as e:
            result.status = AgentStatus.FAILED
            result.success = False
            result.error_message = str(e)
            result.error_details = {
                "type": type(e).__name__,
                "traceback": traceback.format_exc(),
            }
            logger.exception(f"Agent {self.name} failed: {e}")

        finally:
            result.completed_at = datetime.utcnow()
            result.duration_seconds = time.time() - start_time

        self._result = result
        return result

    async def _check_approval_required(self, result: AgentResult) -> Optional[ApprovalGate]:
        """
        Check if human approval is required based on result.

        Override in subclasses for custom approval logic.
        """
        config = self.context.config.agents

        # Check for fatal flaws
        if result.score < config.fatal_flaw_score_threshold:
            return ApprovalGate(
                name="fatal_flaw_review",
                description=f"Score {result.score:.1f} below threshold {config.fatal_flaw_score_threshold}",
                level=ApprovalLevel.APPROVE,
                score_threshold=config.fatal_flaw_score_threshold,
            )

        # Check for high-value opportunities
        if result.score > config.high_value_score_threshold:
            return ApprovalGate(
                name="high_value_review",
                description=f"High-value site detected (score {result.score:.1f})",
                level=ApprovalLevel.NOTIFY,
                score_threshold=config.high_value_score_threshold,
            )

        return None

    async def call_llm(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = True,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call LLM with prompt and return parsed response.

        Args:
            prompt: User prompt
            system: System prompt (uses default if not provided)
            json_mode: Request JSON output
            model: Override model selection

        Returns:
            Parsed response dict
        """
        if not model:
            model = self.context.config.get_llm_model(self.model_tier)

        if not system:
            system = self._get_system_prompt()

        response = await self.llm.complete(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            system=system,
            json_mode=json_mode,
        )

        # Track usage
        self.context.add_tokens(
            response["input_tokens"],
            response["output_tokens"],
            response["model"]
        )

        # Parse JSON response
        content = response["content"]
        if json_mode:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
                if json_match:
                    return json.loads(json_match.group(1))
                # Return as-is if not JSON
                return {"raw_response": content}

        return {"raw_response": content}

    def _get_system_prompt(self) -> str:
        """Get default system prompt for this agent."""
        return f"""You are {self.name}, a specialized AI agent for renewable energy site analysis.

Your role: {self.description}

Guidelines:
- Provide accurate, data-driven analysis
- Quantify confidence levels (0.0-1.0)
- Identify risks and opportunities
- Be concise but thorough
- Always respond in valid JSON format

Output format:
{{
    "analysis": "Your detailed analysis",
    "score": 0-100,
    "confidence": 0.0-1.0,
    "findings": ["key finding 1", "key finding 2"],
    "risks": ["risk 1", "risk 2"],
    "recommendations": ["recommendation 1"],
    "requires_review": false,
    "review_reason": "optional reason if requires_review is true"
}}"""

    def _serialize_output(self, output: Any) -> Dict[str, Any]:
        """Serialize output to dict for storage."""
        if isinstance(output, dict):
            return output
        elif hasattr(output, "to_dict"):
            return output.to_dict()
        elif hasattr(output, "__dict__"):
            return {k: v for k, v in output.__dict__.items() if not k.startswith("_")}
        else:
            return {"value": str(output)}

    async def notify(self, title: str, message: str, data: Optional[Dict] = None):
        """Send notification if callback available."""
        if self.context.on_notification:
            await self.context.on_notification(title, message, data or {})

    async def report_progress(self, progress: float, status: str):
        """Report progress if callback available."""
        if self.context.on_progress:
            await self.context.on_progress(self.name, progress, status)


class ToolAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """
    Agent that uses external tools (APIs, databases, ML models).

    Subclass for agents that primarily call external services
    rather than LLMs.
    """

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool-based analysis."""
        raise NotImplementedError("Subclasses must implement execute()")

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call an external tool.

        Override to implement specific tool integrations.
        """
        raise NotImplementedError(f"Tool {tool_name} not implemented")


class CompositeAgent(BaseAgent[TInput, TOutput]):
    """
    Agent that orchestrates multiple sub-agents.

    Use for complex analyses that require coordination
    between specialized agents.
    """

    def __init__(self, context: Optional[AgentContext] = None):
        super().__init__(context)
        self.sub_agents: List[BaseAgent] = []

    def add_agent(self, agent: BaseAgent) -> None:
        """Add a sub-agent to this composite."""
        agent.context = self.context  # Share context
        self.sub_agents.append(agent)

    async def run_parallel(self, inputs: List[Tuple[BaseAgent, Any]]) -> List[AgentResult]:
        """
        Run multiple agents in parallel.

        Args:
            inputs: List of (agent, input_data) tuples

        Returns:
            List of AgentResults in same order
        """
        tasks = [agent.run(data) for agent, data in inputs]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def run_sequential(self, inputs: List[Tuple[BaseAgent, Any]]) -> List[AgentResult]:
        """
        Run agents sequentially.

        Args:
            inputs: List of (agent, input_data) tuples

        Returns:
            List of AgentResults in same order
        """
        results = []
        for agent, data in inputs:
            result = await agent.run(data)
            results.append(result)
        return results


# Type alias for agent factories
AgentFactory = Callable[[AgentContext], BaseAgent]
