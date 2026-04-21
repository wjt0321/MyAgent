"""Integration tests for MyAgent."""

from __future__ import annotations

from typing import Any, AsyncIterator

import pytest

from myagent.engine.messages import ConversationMessage
from myagent.engine.query_engine import QueryEngine
from myagent.engine.stream_events import (
    AssistantTextDelta,
    AssistantTurnComplete,
    ToolExecutionCompleted,
    ToolExecutionStarted,
)
from myagent.llm.base import BaseProvider
from myagent.llm.types import DoneChunk, StreamChunk, TextChunk, ToolUseChunk
from myagent.tools.bash import Bash
from myagent.tools.read import Read
from myagent.tools.registry import ToolRegistry


class FakeProvider(BaseProvider):
    """Fake LLM provider for integration testing."""

    name = "fake"

    def __init__(self, responses: list[list[StreamChunk]] | None = None) -> None:
        super().__init__(api_key="fake", model="fake")
        self.responses = responses or []
        self.call_count = 0

    async def stream_messages(
        self,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        if self.call_count >= len(self.responses):
            yield TextChunk(text="Done")
            yield DoneChunk()
            return

        response = self.responses[self.call_count]
        self.call_count += 1
        for chunk in response:
            yield chunk

    async def complete(
        self,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        return "Complete"


class TestQueryEngineWithProvider:
    @pytest.mark.asyncio
    async def test_query_engine_with_text_response(self):
        registry = ToolRegistry()
        provider = FakeProvider(responses=[[
            TextChunk(text="Hello!"),
            DoneChunk(),
        ]])

        engine = QueryEngine(
            tool_registry=registry,
            system_prompt="Test",
            llm_client=provider,
        )

        events = []
        async for event in engine.submit_message("Hi"):
            events.append(event)

        text_events = [e for e in events if isinstance(e, AssistantTextDelta)]
        assert len(text_events) == 1
        assert text_events[0].text == "Hello!"

        complete = [e for e in events if isinstance(e, AssistantTurnComplete)]
        assert len(complete) == 1

    @pytest.mark.asyncio
    async def test_query_engine_with_tool_call(self, tmp_path):
        registry = ToolRegistry()
        registry.register(Read())

        test_file = tmp_path / "test.txt"
        test_file.write_text("file content", encoding="utf-8")

        provider = FakeProvider(responses=[
            [
                ToolUseChunk(id="t1", name="Read", input={"path": str(test_file)}),
                DoneChunk(),
            ],
            [
                TextChunk(text="I found the file."),
                DoneChunk(),
            ],
        ])

        engine = QueryEngine(
            tool_registry=registry,
            system_prompt="Test",
            llm_client=provider,
        )

        events = []
        async for event in engine.submit_message("Read the file"):
            events.append(event)

        started = [e for e in events if isinstance(e, ToolExecutionStarted)]
        completed = [e for e in events if isinstance(e, ToolExecutionCompleted)]

        assert len(started) == 1
        assert started[0].tool_name == "Read"
        assert len(completed) == 1
        assert "file content" in completed[0].result

    @pytest.mark.asyncio
    async def test_query_engine_provider_receives_tools(self):
        registry = ToolRegistry()
        registry.register(Bash())

        provider = FakeProvider(responses=[[
            TextChunk(text="OK"),
            DoneChunk(),
        ]])

        engine = QueryEngine(
            tool_registry=registry,
            system_prompt="Test",
            llm_client=provider,
        )

        async for _ in engine.submit_message("Hi"):
            pass

        assert provider.call_count == 1
