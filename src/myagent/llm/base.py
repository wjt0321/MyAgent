"""Base provider for MyAgent LLM integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

from myagent.engine.messages import ConversationMessage
from myagent.llm.types import StreamChunk


class BaseProvider(ABC):
    """Abstract base class for all LLM providers."""

    name: str

    def __init__(self, api_key: str, model: str, base_url: str | None = None, **kwargs: Any) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.extra_kwargs = kwargs

    @abstractmethod
    async def stream_messages(
        self,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream messages from the LLM."""

    @abstractmethod
    async def complete(
        self,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        """Get a complete non-streaming response."""
