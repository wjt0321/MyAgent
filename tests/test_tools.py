"""Tests for myagent tools."""

import asyncio
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


class TestFileTools:
    def test_read_tool_reads_file(self, tmp_path: Path):
        from myagent.tools.read import Read, ReadInput

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world", encoding="utf-8")

        tool = Read()
        ctx = ToolExecutionContext(cwd=tmp_path)
        result = asyncio.run(tool.execute(ReadInput(path=str(test_file)), ctx))

        assert result.output == "hello world"
        assert result.is_error is False

    def test_read_tool_file_not_found(self, tmp_path: Path):
        from myagent.tools.read import Read, ReadInput

        tool = Read()
        ctx = ToolExecutionContext(cwd=tmp_path)
        result = asyncio.run(tool.execute(ReadInput(path="nonexistent.txt"), ctx))

        assert result.is_error is True
        assert "not found" in result.output.lower() or "does not exist" in result.output.lower()

    def test_read_tool_is_read_only(self):
        from myagent.tools.read import Read

        tool = Read()
        assert tool.is_read_only(None) is True

    def test_write_tool_creates_file(self, tmp_path: Path):
        from myagent.tools.write import Write, WriteInput

        tool = Write()
        ctx = ToolExecutionContext(cwd=tmp_path)
        result = asyncio.run(
            tool.execute(WriteInput(path="new_file.txt", content="new content"), ctx)
        )

        assert result.is_error is False
        assert (tmp_path / "new_file.txt").read_text(encoding="utf-8") == "new content"

    def test_write_tool_overwrites_file(self, tmp_path: Path):
        from myagent.tools.write import Write, WriteInput

        test_file = tmp_path / "existing.txt"
        test_file.write_text("old content", encoding="utf-8")

        tool = Write()
        ctx = ToolExecutionContext(cwd=tmp_path)
        result = asyncio.run(
            tool.execute(WriteInput(path="existing.txt", content="new content"), ctx)
        )

        assert result.is_error is False
        assert test_file.read_text(encoding="utf-8") == "new content"

    def test_edit_tool_replaces_text(self, tmp_path: Path):
        from myagent.tools.edit import Edit, EditInput

        test_file = tmp_path / "edit_me.txt"
        test_file.write_text("hello old world", encoding="utf-8")

        tool = Edit()
        ctx = ToolExecutionContext(cwd=tmp_path)
        result = asyncio.run(
            tool.execute(
                EditInput(path="edit_me.txt", old_string="old", new_string="new"), ctx
            )
        )

        assert result.is_error is False
        assert test_file.read_text(encoding="utf-8") == "hello new world"

    def test_edit_tool_old_string_not_found(self, tmp_path: Path):
        from myagent.tools.edit import Edit, EditInput

        test_file = tmp_path / "edit_me.txt"
        test_file.write_text("hello world", encoding="utf-8")

        tool = Edit()
        ctx = ToolExecutionContext(cwd=tmp_path)
        result = asyncio.run(
            tool.execute(
                EditInput(path="edit_me.txt", old_string="nonexistent", new_string="new"),
                ctx,
            )
        )

        assert result.is_error is True
        assert "not found" in result.output.lower()


class TestShellAndSearchTools:
    def test_bash_tool_echo(self, tmp_path: Path):
        from myagent.tools.bash import Bash, BashInput

        tool = Bash()
        ctx = ToolExecutionContext(cwd=tmp_path)
        result = asyncio.run(tool.execute(BashInput(command="echo hello"), ctx))

        assert result.is_error is False
        assert "hello" in result.output

    def test_bash_tool_invalid_command(self, tmp_path: Path):
        from myagent.tools.bash import Bash, BashInput

        tool = Bash()
        ctx = ToolExecutionContext(cwd=tmp_path)
        result = asyncio.run(tool.execute(BashInput(command="this_command_does_not_exist_12345"), ctx))

        assert result.is_error is True

    def test_glob_tool_matches(self, tmp_path: Path):
        from myagent.tools.glob import Glob, GlobInput

        (tmp_path / "a.py").write_text("", encoding="utf-8")
        (tmp_path / "b.py").write_text("", encoding="utf-8")
        (tmp_path / "c.txt").write_text("", encoding="utf-8")

        tool = Glob()
        ctx = ToolExecutionContext(cwd=tmp_path)
        result = asyncio.run(tool.execute(GlobInput(pattern="*.py"), ctx))

        assert result.is_error is False
        assert "a.py" in result.output
        assert "b.py" in result.output
        assert "c.txt" not in result.output

    def test_glob_tool_is_read_only(self):
        from myagent.tools.glob import Glob

        tool = Glob()
        assert tool.is_read_only(None) is True

    def test_grep_tool_finds_matches(self, tmp_path: Path):
        from myagent.tools.grep import Grep, GrepInput

        (tmp_path / "file1.py").write_text("def hello(): pass\n", encoding="utf-8")
        (tmp_path / "file2.py").write_text("def world(): pass\n", encoding="utf-8")

        tool = Grep()
        ctx = ToolExecutionContext(cwd=tmp_path)
        result = asyncio.run(tool.execute(GrepInput(pattern="hello", glob="*.py"), ctx))

        assert result.is_error is False
        assert "file1.py" in result.output
        assert "hello" in result.output
        assert "file2.py" not in result.output

    def test_grep_tool_is_read_only(self):
        from myagent.tools.grep import Grep

        tool = Grep()
        assert tool.is_read_only(None) is True
