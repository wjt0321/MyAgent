"""Tests for TodoWrite tool (task management)."""

import asyncio
import json
from pathlib import Path

import pytest

from myagent.tools.base import ToolExecutionContext, ToolResult
from myagent.tools.todo import TodoWrite, TodoWriteInput


class TestTodoWriteTool:
    def test_todo_write_creation(self):
        tool = TodoWrite()
        assert tool.name == "TodoWrite"
        assert "todo" in tool.description.lower() or "task" in tool.description.lower()

    def test_todo_write_is_read_only(self):
        tool = TodoWrite()
        assert tool.is_read_only(None) is False

    @pytest.mark.asyncio
    async def test_todo_write_create_task(self, tmp_path: Path):
        tool = TodoWrite()
        ctx = ToolExecutionContext(cwd=tmp_path)

        result = await tool.execute(
            TodoWriteInput(
                action="create",
                title="Implement login",
                description="Add user authentication",
            ),
            ctx,
        )

        assert result.is_error is False
        assert "created" in result.output.lower() or "Implement login" in result.output

        todo_file = tmp_path / ".myagent" / "todos.json"
        assert todo_file.exists()
        data = json.loads(todo_file.read_text(encoding="utf-8"))
        assert len(data["todos"]) == 1
        assert data["todos"][0]["title"] == "Implement login"
        assert data["todos"][0]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_todo_write_list_tasks(self, tmp_path: Path):
        tool = TodoWrite()
        ctx = ToolExecutionContext(cwd=tmp_path)

        await tool.execute(
            TodoWriteInput(action="create", title="Task 1"),
            ctx,
        )
        await tool.execute(
            TodoWriteInput(action="create", title="Task 2"),
            ctx,
        )

        result = await tool.execute(
            TodoWriteInput(action="list"),
            ctx,
        )

        assert result.is_error is False
        assert "Task 1" in result.output
        assert "Task 2" in result.output

    @pytest.mark.asyncio
    async def test_todo_write_update_status(self, tmp_path: Path):
        tool = TodoWrite()
        ctx = ToolExecutionContext(cwd=tmp_path)

        create_result = await tool.execute(
            TodoWriteInput(action="create", title="Task to update"),
            ctx,
        )
        task_id = json.loads(create_result.metadata.get("task", "{}")).get("id")

        result = await tool.execute(
            TodoWriteInput(action="update", task_id=task_id, status="in_progress"),
            ctx,
        )

        assert result.is_error is False
        assert "in_progress" in result.output or "updated" in result.output.lower()

        todo_file = tmp_path / ".myagent" / "todos.json"
        data = json.loads(todo_file.read_text(encoding="utf-8"))
        assert data["todos"][0]["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_todo_write_complete_task(self, tmp_path: Path):
        tool = TodoWrite()
        ctx = ToolExecutionContext(cwd=tmp_path)

        create_result = await tool.execute(
            TodoWriteInput(action="create", title="Task to complete"),
            ctx,
        )
        task_id = json.loads(create_result.metadata.get("task", "{}")).get("id")

        result = await tool.execute(
            TodoWriteInput(action="update", task_id=task_id, status="completed"),
            ctx,
        )

        assert result.is_error is False

        todo_file = tmp_path / ".myagent" / "todos.json"
        data = json.loads(todo_file.read_text(encoding="utf-8"))
        assert data["todos"][0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_todo_write_delete_task(self, tmp_path: Path):
        tool = TodoWrite()
        ctx = ToolExecutionContext(cwd=tmp_path)

        create_result = await tool.execute(
            TodoWriteInput(action="create", title="Task to delete"),
            ctx,
        )
        task_id = json.loads(create_result.metadata.get("task", "{}")).get("id")

        result = await tool.execute(
            TodoWriteInput(action="delete", task_id=task_id),
            ctx,
        )

        assert result.is_error is False

        todo_file = tmp_path / ".myagent" / "todos.json"
        data = json.loads(todo_file.read_text(encoding="utf-8"))
        assert len(data["todos"]) == 0

    @pytest.mark.asyncio
    async def test_todo_write_update_nonexistent(self, tmp_path: Path):
        tool = TodoWrite()
        ctx = ToolExecutionContext(cwd=tmp_path)

        result = await tool.execute(
            TodoWriteInput(action="update", task_id="nonexistent-id", status="completed"),
            ctx,
        )

        assert result.is_error is True
        assert "not found" in result.output.lower()

    @pytest.mark.asyncio
    async def test_todo_write_invalid_action(self, tmp_path: Path):
        tool = TodoWrite()
        ctx = ToolExecutionContext(cwd=tmp_path)

        result = await tool.execute(
            TodoWriteInput(action="invalid_action"),
            ctx,
        )

        assert result.is_error is True
        assert "invalid" in result.output.lower() or "unknown" in result.output.lower()

    @pytest.mark.asyncio
    async def test_todo_write_clear_completed(self, tmp_path: Path):
        tool = TodoWrite()
        ctx = ToolExecutionContext(cwd=tmp_path)

        r1 = await tool.execute(TodoWriteInput(action="create", title="Task A"), ctx)
        r2 = await tool.execute(TodoWriteInput(action="create", title="Task B"), ctx)
        id_a = json.loads(r1.metadata.get("task", "{}")).get("id")
        id_b = json.loads(r2.metadata.get("task", "{}")).get("id")

        await tool.execute(TodoWriteInput(action="update", task_id=id_a, status="completed"), ctx)

        result = await tool.execute(TodoWriteInput(action="clear_completed"), ctx)

        assert result.is_error is False

        todo_file = tmp_path / ".myagent" / "todos.json"
        data = json.loads(todo_file.read_text(encoding="utf-8"))
        assert len(data["todos"]) == 1
        assert data["todos"][0]["id"] == id_b
