"""OpenAI Chat Completions API provider for MyAgent."""

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


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI's Chat Completions API."""

    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.openai.com/v1",
            **kwargs,
        )

    def _convert_messages(
        self, messages: list[ConversationMessage]
    ) -> list[dict[str, Any]]:
        """Convert internal messages to OpenAI format."""
        openai_messages = []

        for msg in messages:
            content = ""
            tool_calls = []
            tool_call_id = None

            for block in msg.content:
                if isinstance(block, TextBlock):
                    content += block.text
                elif isinstance(block, ToolUseBlock):
                    tool_calls.append({
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": block.name,
                            "arguments": json.dumps(block.input),
                        },
                    })
                elif isinstance(block, ToolResultBlock):
                    tool_call_id = block.tool_use_id
                    content = block.content

            openai_msg: dict[str, Any] = {"role": msg.role}

            if tool_calls:
                openai_msg["content"] = content or None
                openai_msg["tool_calls"] = tool_calls
            elif tool_call_id:
                openai_msg["role"] = "tool"
                openai_msg["tool_call_id"] = tool_call_id
                openai_msg["content"] = str(content)
            else:
                openai_msg["content"] = content or msg.text

            openai_messages.append(openai_msg)

        return openai_messages

    def _convert_tools(self, tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        """Convert tool schemas to OpenAI format."""
        if not tools:
            return None

        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool.get("input_schema", tool.get("parameters", {})),
                },
            })
        return openai_tools

    def _parse_event(self, event: dict[str, Any]) -> StreamChunk | None:
        """Parse an OpenAI SSE event into a StreamChunk."""
        choices = event.get("choices", [])
        if not choices:
            return None

        delta = choices[0].get("delta", {})
        finish_reason = choices[0].get("finish_reason")

        if finish_reason:
            return DoneChunk()

        if "content" in delta and delta["content"]:
            return TextChunk(text=delta["content"])

        if "tool_calls" in delta and delta["tool_calls"]:
            tc = delta["tool_calls"][0]
            func = tc.get("function", {})
            args = func.get("arguments", "{}")
            try:
                parsed_args = json.loads(args) if args else {}
            except json.JSONDecodeError:
                parsed_args = {}

            return ToolUseChunk(
                id=tc.get("id", ""),
                name=func.get("name", ""),
                input=parsed_args,
            )

        return None

    async def stream_messages(
        self,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream messages from OpenAI's API."""
        openai_messages = self._convert_messages(messages)
        openai_tools = self._convert_tools(tools)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": openai_messages,
            "stream": True,
        }
        if openai_tools:
            payload["tools"] = openai_tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
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
        openai_messages = self._convert_messages(messages)
        openai_tools = self._convert_tools(tools)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": openai_messages,
            "stream": False,
        }
        if openai_tools:
            payload["tools"] = openai_tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

            message = data.get("choices", [{}])[0].get("message", {})
            return message.get("content", "")
