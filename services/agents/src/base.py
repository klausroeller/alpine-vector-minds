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
