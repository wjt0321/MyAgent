"""Tests for QueryEngine."""

from __future__ import annotations

from typing import Any, AsyncIterator

import pytest

from myagent.engine.messages import (
    ConversationMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
)
from myagent.engine.query_engine import MaxTurnsExceeded, QueryEngine
from myagent.engine.stream_events import (
    AssistantTextDelta,
    AssistantTurnComplete,
    ToolExecutionCompleted,
    ToolExecutionStarted,
)
from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult
from myagent.tools.registry import ToolRegistry
from pydantic import BaseModel


class FakeInput(BaseModel):
    message: str = ""


class FakeTool(BaseTool):
    name = "fake_tool"
    description = "A fake tool"
    input_model = FakeInput

    async def execute(self, arguments: FakeInput, context: ToolExecutionContext) -> ToolResult:
        return ToolResult(output=f"Result: {arguments.message}")


class FakeLLMClient:
    """Fake LLM client for testing."""

    def __init__(self, responses: list[list[Any]] | None = None) -> None:
        self.responses = responses or []
        self.call_count = 0

    async def stream_messages(
        self,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]],
    ) -> AsyncIterator[Any]:
        if self.call_count >= len(self.responses):
            yield type("obj", (object,), {"type": "text", "text": "Done"})()
            return

        response = self.responses[self.call_count]
        self.call_count += 1
        for item in response:
            yield item


class TestQueryEngine:
    def test_query_engine_creation(self):
        registry = ToolRegistry()
        registry.register(FakeTool())

        engine = QueryEngine(
            tool_registry=registry,
            system_prompt="You are a test agent.",
            max_turns=5,
        )

        assert engine.max_turns == 5
        assert len(engine.messages) == 1  # system message

    def test_query_engine_adds_system_message(self):
        registry = ToolRegistry()
        engine = QueryEngine(
            tool_registry=registry,
            system_prompt="System prompt here",
        )

        assert engine.messages[0].role == "system"
        assert engine.messages[0].text == "System prompt here"

    @pytest.mark.asyncio
    async def test_query_engine_basic_text_response(self):
        registry = ToolRegistry()

        fake_client = FakeLLMClient(responses=[[
            type("Event", (), {"type": "text", "text": "Hello user"})(),
        ]])

        engine = QueryEngine(
            tool_registry=registry,
            system_prompt="Test",
            llm_client=fake_client,
        )

        events = []
        async for event in engine.submit_message("Hi"):
            events.append(event)

        text_events = [e for e in events if isinstance(e, AssistantTextDelta)]
        assert len(text_events) == 1
        assert text_events[0].text == "Hello user"

    @pytest.mark.asyncio
    async def test_query_engine_tool_loop(self):
        registry = ToolRegistry()
        registry.register(FakeTool())

        fake_client = FakeLLMClient(responses=[
            [
                type("Event", (), {
                    "type": "tool_use",
                    "id": "t1",
                    "name": "fake_tool",
                    "input": {"message": "test"},
                })(),
            ],
            [
                type("Event", (), {"type": "text", "text": "Done with tool"})(),
            ],
        ])

        engine = QueryEngine(
            tool_registry=registry,
            system_prompt="Test",
            llm_client=fake_client,
        )

        events = []
        async for event in engine.submit_message("Call tool"):
            events.append(event)

        started = [e for e in events if isinstance(e, ToolExecutionStarted)]
        completed = [e for e in events if isinstance(e, ToolExecutionCompleted)]

        assert len(started) == 1
        assert started[0].tool_name == "fake_tool"
        assert len(completed) == 1
        assert completed[0].result == "Result: test"

    @pytest.mark.asyncio
    async def test_query_engine_max_turns(self):
        registry = ToolRegistry()
        registry.register(FakeTool())

        fake_client = FakeLLMClient(responses=[
            [
                type("Event", (), {
                    "type": "tool_use",
                    "id": f"t{i}",
                    "name": "fake_tool",
                    "input": {"message": f"test{i}"},
                })(),
            ]
            for i in range(5)
        ])

        engine = QueryEngine(
            tool_registry=registry,
            system_prompt="Test",
            llm_client=fake_client,
            max_turns=3,
        )

        with pytest.raises(MaxTurnsExceeded):
            async for _ in engine.submit_message("Call tool repeatedly"):
                pass

    @pytest.mark.asyncio
    async def test_query_engine_turn_complete_event(self):
        registry = ToolRegistry()

        fake_client = FakeLLMClient(responses=[[
            type("Event", (), {"type": "text", "text": "Response"})(),
        ]])

        engine = QueryEngine(
            tool_registry=registry,
            system_prompt="Test",
            llm_client=fake_client,
        )

        events = []
        async for event in engine.submit_message("Hi"):
            events.append(event)

        complete = [e for e in events if isinstance(e, AssistantTurnComplete)]
        assert len(complete) == 1
        assert complete[0].message.role == "assistant"
