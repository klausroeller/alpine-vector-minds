from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class AgentMessage(BaseModel):
    role: str
    content: str


class AgentResponse(BaseModel):
    content: str
    metadata: dict[str, Any] = {}


class BaseAgent(ABC):
    """Base class for AI agents."""

    @abstractmethod
    async def run(self, messages: list[AgentMessage]) -> AgentResponse:
        """Execute the agent with the given messages."""
        pass


def strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences from LLM responses."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0]
    return text.strip()
