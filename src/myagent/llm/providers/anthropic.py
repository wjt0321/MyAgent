"""Anthropic Messages API provider for MyAgent."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx

from myagent.engine.messages import (
    ConversationMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
)
from myagent.llm.base import BaseProvider
from myagent.llm.types import DoneChunk, StreamChunk, TextChunk, ToolUseChunk


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic's Messages API."""

    name = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-sonnet-20240229",
        base_url: str | None = None,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.anthropic.com",
            **kwargs,
        )
        self.max_tokens = max_tokens

    def _convert_messages(
        self, messages: list[ConversationMessage]
    ) -> dict[str, Any]:
        """Convert internal messages to Anthropic format."""
        system_text = ""
        anthropic_messages = []

        for msg in messages:
            if msg.role == "system":
                system_text = msg.text
                continue

            content = []
            for block in msg.content:
                if isinstance(block, TextBlock):
                    content.append({"type": "text", "text": block.text})
                elif isinstance(block, ToolUseBlock):
                    content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
                elif isinstance(block, ToolResultBlock):
                    content.append({
                        "type": "tool_result",
                        "tool_use_id": block.tool_use_id,
                        "content": block.content,
                        "is_error": block.is_error,
                    })

            if not content and msg.text:
                content = [{"type": "text", "text": msg.text}]

            anthropic_messages.append({"role": msg.role, "content": content})

        result: dict[str, Any] = {"messages": anthropic_messages}
        if system_text:
            result["system"] = system_text
        return result

    def _convert_tools(self, tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        """Convert tool schemas to Anthropic format."""
        if not tools:
            return None

        anthropic_tools = []
        for tool in tools:
            anthropic_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool.get("input_schema", tool.get("parameters", {})),
            })
        return anthropic_tools

    def _parse_event(self, event: dict[str, Any]) -> StreamChunk | None:
        """Parse an Anthropic SSE event into a StreamChunk."""
        event_type = event.get("type")

        if event_type == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                return TextChunk(text=delta.get("text", ""))

        elif event_type == "content_block_start":
            block = event.get("content_block", {})
            if block.get("type") == "tool_use":
                return ToolUseChunk(
                    id=block.get("id", ""),
                    name=block.get("name", ""),
                    input=block.get("input", {}),
                )

        elif event_type == "message_stop":
            return DoneChunk()

        return None

    async def stream_messages(
        self,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream messages from Anthropic's API."""
        converted = self._convert_messages(messages)
        anthropic_tools = self._convert_tools(tools)

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": converted["messages"],
            "stream": True,
        }
        if "system" in converted:
            payload["system"] = converted["system"]
        if anthropic_tools:
            payload["tools"] = anthropic_tools

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
                timeout=60.0,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue

                    data = line[6:]
                    if data == "[DONE]":
                        yield DoneChunk()
                        return

                    try:
                        event = json.loads(data)
                        chunk = self._parse_event(event)
                        if chunk:
                            yield chunk
                    except json.JSONDecodeError:
                        continue

    async def complete(
        self,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        """Get a complete non-streaming response."""
        converted = self._convert_messages(messages)
        anthropic_tools = self._convert_tools(tools)

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": converted["messages"],
            "stream": False,
        }
        if "system" in converted:
            payload["system"] = converted["system"]
        if anthropic_tools:
            payload["tools"] = anthropic_tools

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

            parts = []
            for block in data.get("content", []):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return "\n".join(parts)
