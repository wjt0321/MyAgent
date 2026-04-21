"""Tests for AgentTool (sub-agent invocation)."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from myagent.agents.definitions import AgentDefinition
from myagent.tools.agent_tool import AgentTool, AgentToolInput
from myagent.tools.base import ToolExecutionContext, ToolResult


class MockAsyncIterator:
    """Helper to mock async iterators."""

    def __init__(self, items: list) -> None:
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


class TestAgentTool:
    def test_agent_tool_creation(self):
        tool = AgentTool()
        assert tool.name == "AgentTool"
        assert "agent" in tool.description.lower()

    def test_agent_tool_is_read_only(self):
        tool = AgentTool()
        assert tool.is_read_only(None) is False

    @pytest.mark.asyncio
    async def test_agent_tool_invokes_sub_agent(self):
        tool = AgentTool()
        ctx = ToolExecutionContext(cwd=Path("."))

        mock_agent_def = AgentDefinition(
            name="code-explorer",
            description="Code exploration agent",
            system_prompt="You are a code explorer.",
            tools=["Read", "Glob", "Grep"],
            max_turns=10,
        )

        mock_event1 = MagicMock()
        mock_event1.text = "Found the function in "
        mock_event2 = MagicMock()
        mock_event2.text = "src/main.py"

        mock_engine = MagicMock()
        mock_engine.submit_message.return_value = MockAsyncIterator([mock_event1, mock_event2])

        with patch("myagent.tools.agent_tool.AgentLoader") as MockLoader:
            mock_loader = MagicMock()
            mock_loader.load_builtin_agents.return_value = {"code-explorer": mock_agent_def}
            mock_loader.load_all.return_value = {}
            MockLoader.return_value = mock_loader

            with patch("myagent.tools.agent_tool.QueryEngine", return_value=mock_engine):
                result = await tool.execute(
                    AgentToolInput(agent="code-explorer", task="Find the main function"),
                    ctx,
                )

        assert result.is_error is False
        assert "Found the function" in result.output
        assert "src/main.py" in result.output
        mock_engine.submit_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_tool_agent_not_found(self):
        tool = AgentTool()
        ctx = ToolExecutionContext(cwd=Path("."))

        with patch("myagent.tools.agent_tool.AgentLoader") as MockLoader:
            mock_loader = MagicMock()
            mock_loader.load_builtin_agents.return_value = {}
            mock_loader.load_all.return_value = {}
            MockLoader.return_value = mock_loader

            result = await tool.execute(
                AgentToolInput(agent="nonexistent", task="Do something"),
                ctx,
            )

        assert result.is_error is True
        assert "not found" in result.output.lower()

    @pytest.mark.asyncio
    async def test_agent_tool_with_custom_model(self):
        tool = AgentTool()
        ctx = ToolExecutionContext(cwd=Path("."))

        mock_agent_def = AgentDefinition(
            name="planner",
            description="Planning agent",
            system_prompt="You are a planner.",
            model="gpt-4o",
            max_turns=5,
        )

        mock_event = MagicMock()
        mock_event.text = "Plan created"

        mock_engine = MagicMock()
        mock_engine.submit_message.return_value = MockAsyncIterator([mock_event])

        with patch("myagent.tools.agent_tool.AgentLoader") as MockLoader:
            mock_loader = MagicMock()
            mock_loader.load_builtin_agents.return_value = {"planner": mock_agent_def}
            mock_loader.load_all.return_value = {}
            MockLoader.return_value = mock_loader

            with patch("myagent.tools.agent_tool.QueryEngine", return_value=mock_engine):
                result = await tool.execute(
                    AgentToolInput(
                        agent="planner",
                        task="Create a plan",
                        model="claude-sonnet",
                    ),
                    ctx,
                )

        assert result.is_error is False
        assert "Plan created" in result.output

    @pytest.mark.asyncio
    async def test_agent_tool_engine_error(self):
        tool = AgentTool()
        ctx = ToolExecutionContext(cwd=Path("."))

        mock_agent_def = AgentDefinition(
            name="worker",
            description="Worker agent",
            system_prompt="You are a worker.",
        )

        mock_engine = MagicMock()
        mock_engine.submit_message.side_effect = Exception("Engine failed")

        with patch("myagent.tools.agent_tool.AgentLoader") as MockLoader:
            mock_loader = MagicMock()
            mock_loader.load_builtin_agents.return_value = {"worker": mock_agent_def}
            mock_loader.load_all.return_value = {}
            MockLoader.return_value = mock_loader

            with patch("myagent.tools.agent_tool.QueryEngine", return_value=mock_engine):
                result = await tool.execute(
                    AgentToolInput(agent="worker", task="Do work"),
                    ctx,
                )

        assert result.is_error is True
        assert "Engine failed" in result.output

    @pytest.mark.asyncio
    async def test_agent_tool_no_llm_client(self):
        tool = AgentTool()
        ctx = ToolExecutionContext(cwd=Path("."))

        mock_agent_def = AgentDefinition(
            name="helper",
            description="Helper agent",
            system_prompt="You are a helper.",
        )

        mock_event = MagicMock()
        mock_event.text = "Result without LLM"

        mock_engine = MagicMock()
        mock_engine.submit_message.return_value = MockAsyncIterator([mock_event])

        with patch("myagent.tools.agent_tool.AgentLoader") as MockLoader:
            mock_loader = MagicMock()
            mock_loader.load_builtin_agents.return_value = {"helper": mock_agent_def}
            mock_loader.load_all.return_value = {}
            MockLoader.return_value = mock_loader

            with patch("myagent.tools.agent_tool.QueryEngine", return_value=mock_engine):
                result = await tool.execute(
                    AgentToolInput(agent="helper", task="Help me"),
                    ctx,
                )

        assert result.is_error is False
        assert "Result without LLM" in result.output
