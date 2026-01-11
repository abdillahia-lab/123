"""
Base Agent - Foundation for all Paces AI agents.

Provides common functionality for LLM-powered analysis agents.
"""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from loguru import logger


@dataclass
class AgentResult:
    """Result from an agent execution."""
    agent_name: str
    task_id: str = field(default_factory=lambda: str(uuid4())[:8])

    success: bool = True
    error: Optional[str] = None

    # Results
    data: dict = field(default_factory=dict)
    analysis: str = ""
    confidence: float = 0.0

    # Recommendations
    recommendations: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    # Metadata
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Token usage
    tokens_used: int = 0
    model_used: str = ""

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "task_id": self.task_id,
            "success": self.success,
            "error": self.error,
            "data": self.data,
            "analysis": self.analysis,
            "confidence": self.confidence,
            "recommendations": self.recommendations,
            "risks": self.risks,
            "duration_seconds": self.duration_seconds,
        }


class BaseAgent(ABC):
    """
    Base class for all Paces AI agents.

    Provides:
    - LLM integration (Claude, GPT-4, etc.)
    - Structured prompting
    - Result parsing
    - Error handling
    - Logging and metrics
    """

    def __init__(
        self,
        name: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ):
        self.name = name
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self._client = None
        self._initialized = False

        logger.info(f"Agent '{name}' created with model {model}")

    async def initialize(self) -> bool:
        """Initialize the agent with LLM client."""
        try:
            # Initialize LLM client (Claude via Anthropic SDK)
            # In production, this would use actual API client
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
            return True

        except Exception as e:
            logger.error(f"Agent '{self.name}' initialization failed: {e}")
            return False

    @abstractmethod
    async def execute(self, **kwargs) -> AgentResult:
        """Execute the agent's main task."""
        pass

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
    ) -> tuple[str, int]:
        """
        Call the LLM with the given prompts.

        Returns:
            Tuple of (response_text, tokens_used)
        """
        try:
            # In production, this would use actual API
            # For now, simulate response based on prompt content
            response = await self._simulate_llm_response(
                system_prompt, user_prompt, json_mode
            )
            tokens = len(system_prompt.split()) + len(user_prompt.split()) + len(response.split())
            return response, tokens

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    async def _simulate_llm_response(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool,
    ) -> str:
        """Simulate LLM response for development/testing."""
        # This would be replaced with actual API call
        await asyncio.sleep(0.1)  # Simulate latency

        if json_mode:
            return json.dumps({
                "analysis": "Simulated analysis from LLM",
                "confidence": 0.85,
                "recommendations": ["Recommendation 1", "Recommendation 2"],
            })
        return "Simulated analysis from LLM"

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response."""
        try:
            # Try to extract JSON from response
            if "```json" in response:
                start = response.index("```json") + 7
                end = response.index("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.index("```") + 3
                end = response.index("```", start)
                response = response[start:end].strip()

            return json.loads(response)

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return {"raw_response": response}

    def _build_result(
        self,
        success: bool = True,
        error: str = None,
        data: dict = None,
        analysis: str = "",
        confidence: float = 0.0,
        recommendations: list = None,
        risks: list = None,
        tokens: int = 0,
        start_time: datetime = None,
    ) -> AgentResult:
        """Build a standardized agent result."""
        now = datetime.now()
        duration = (now - start_time).total_seconds() if start_time else 0

        return AgentResult(
            agent_name=self.name,
            success=success,
            error=error,
            data=data or {},
            analysis=analysis,
            confidence=confidence,
            recommendations=recommendations or [],
            risks=risks or [],
            started_at=start_time or now,
            completed_at=now,
            duration_seconds=duration,
            tokens_used=tokens,
            model_used=self.model,
        )
