"""Tests for myagent tools."""

from pathlib import Path

import pytest
from pydantic import BaseModel

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult
from myagent.tools.registry import ToolRegistry


class DummyInput(BaseModel):
    message: str


class DummyTool(BaseTool):
    name = "dummy"
    description = "A dummy tool for testing"
    input_model = DummyInput

    async def execute(self, arguments: DummyInput, context: ToolExecutionContext) -> ToolResult:
        return ToolResult(output=f"Echo: {arguments.message}")


class ReadOnlyTool(BaseTool):
    name = "readonly"
    description = "A read-only tool"
    input_model = DummyInput

    async def execute(self, arguments: DummyInput, context: ToolExecutionContext) -> ToolResult:
        return ToolResult(output="readonly result")

    def is_read_only(self, arguments: BaseModel) -> bool:
        return True


class TestToolBaseClass:
    def test_tool_has_required_attributes(self):
        tool = DummyTool()
        assert tool.name == "dummy"
        assert tool.description == "A dummy tool for testing"
        assert tool.input_model == DummyInput

    def test_tool_default_read_only(self):
        tool = DummyTool()
        assert tool.is_read_only(DummyInput(message="test")) is False

    def test_read_only_tool(self):
        tool = ReadOnlyTool()
        assert tool.is_read_only(DummyInput(message="test")) is True

    def test_tool_api_schema(self):
        tool = DummyTool()
        schema = tool.to_api_schema()
        assert schema["name"] == "dummy"
        assert schema["description"] == "A dummy tool for testing"
        assert "input_schema" in schema


class TestToolRegistry:
    def test_register_tool(self):
        registry = ToolRegistry()
        tool = DummyTool()
        registry.register(tool)
        assert registry.get("dummy") is tool

    def test_get_nonexistent_tool(self):
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_list_tools(self):
        registry = ToolRegistry()
        registry.register(DummyTool())
        registry.register(ReadOnlyTool())
        tools = registry.list_tools()
        assert len(tools) == 2
        assert any(t.name == "dummy" for t in tools)
        assert any(t.name == "readonly" for t in tools)

    def test_to_api_schema(self):
        registry = ToolRegistry()
        registry.register(DummyTool())
        schemas = registry.to_api_schema()
        assert len(schemas) == 1
        assert schemas[0]["name"] == "dummy"

    def test_duplicate_registration_overwrites(self):
        registry = ToolRegistry()
        tool1 = DummyTool()
        tool2 = DummyTool()
        registry.register(tool1)
        registry.register(tool2)
        assert registry.get("dummy") is tool2
