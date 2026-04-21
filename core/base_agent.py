"""
BaseAgent - abstract class all AI agents inherit from.
Supports both OpenAI and Anthropic. Switch with LLM_PROVIDER env var.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, AsyncIterator

import structlog
import yaml
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

logger = structlog.get_logger()


class AgentOutput(BaseModel):
    content: str
    quality_score: float = 0.0
    tokens_used: int = 0
    model: str = ""
    agent_type: str = ""
    metadata: dict[str, Any] = {}


class BaseAgent(ABC):

    def __init__(self):
        self.llm = self._create_llm()
        self.prompts = self._load_prompts()
        self.logger = logger.bind(agent=self.agent_type)

    @property
    @abstractmethod
    def agent_type(self) -> str:
        ...

    @property
    @abstractmethod
    def prompt_file(self) -> str:
        ...

    def _create_llm(self):
        if settings.is_openai:
            return ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0.7,
                max_tokens=4096,
            )
        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0.7,
            max_tokens=4096,
        )

    def _load_prompts(self) -> dict:
        prompt_path = Path(self.prompt_file)
        if not prompt_path.exists():
            self.logger.warning("Prompt file not found", path=str(prompt_path))
            return {}
        with open(prompt_path) as f:
            return yaml.safe_load(f)

    def _build_messages(self, system_prompt: str, user_prompt: str) -> list:
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

    def _render(self, key: str, **kwargs) -> str:
        template = self.prompts.get(key, "")
        if not template:
            raise ValueError(f"Template '{key}' not found in {self.prompt_file}")
        return template.format(**kwargs)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        messages = self._build_messages(system_prompt, user_prompt)
        self.logger.info("Calling LLM", provider=settings.llm_provider, model=settings.active_model)
        response = await self.llm.ainvoke(messages)
        return response.content

    async def _stream_llm(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        messages = self._build_messages(system_prompt, user_prompt)
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield chunk.content

    @abstractmethod
    async def run(self, input_data: dict[str, Any]) -> AgentOutput:
        ...

    @abstractmethod
    async def run_stream(self, input_data: dict[str, Any]) -> AsyncIterator[str]:
        ...
