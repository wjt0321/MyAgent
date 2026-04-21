"""TodoWrite tool for MyAgent - task management."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


class TodoWriteInput(BaseModel):
    action: str = Field(
        description="Action to perform: create, list, update, delete, clear_completed"
    )
    task_id: str | None = Field(default=None, description="Task ID (required for update/delete)")
    title: str | None = Field(default=None, description="Task title (required for create)")
    description: str | None = Field(default=None, description="Optional task description")
    status: str | None = Field(
        default=None,
        description="Status: pending, in_progress, completed (for update)",
    )


class TodoWrite(BaseTool):
    name = "TodoWrite"
    description = (
        "Manage a todo/task list for tracking progress. "
        "Actions: create (add task), list (show all), update (change status), "
        "delete (remove task), clear_completed (remove done tasks)."
    )
    input_model = TodoWriteInput

    def _get_todo_path(self, cwd: Path) -> Path:
        todo_dir = cwd / ".myagent"
        todo_dir.mkdir(parents=True, exist_ok=True)
        return todo_dir / "todos.json"

    def _load_todos(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {"todos": []}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"todos": []}

    def _save_todos(self, path: Path, data: dict[str, Any]) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def execute(
        self, arguments: TodoWriteInput, context: ToolExecutionContext
    ) -> ToolResult:
        todo_path = self._get_todo_path(context.cwd)
        data = self._load_todos(todo_path)
        action = arguments.action.lower().strip()

        if action == "create":
            return self._do_create(data, arguments, todo_path)
        elif action == "list":
            return self._do_list(data)
        elif action == "update":
            return self._do_update(data, arguments, todo_path)
        elif action == "delete":
            return self._do_delete(data, arguments, todo_path)
        elif action == "clear_completed":
            return self._do_clear_completed(data, todo_path)
        else:
            return ToolResult(
                output=f"Error: Unknown action '{arguments.action}'. "
                "Valid actions: create, list, update, delete, clear_completed",
                is_error=True,
            )

    def _do_create(
        self, data: dict[str, Any], arguments: TodoWriteInput, path: Path
    ) -> ToolResult:
        title = (arguments.title or "").strip()
        if not title:
            return ToolResult(
                output="Error: 'title' is required for create action.",
                is_error=True,
            )

        task = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "description": (arguments.description or "").strip(),
            "status": "pending",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        data["todos"].append(task)
        self._save_todos(path, data)

        return ToolResult(
            output=f"Created task: [{task['id']}] {task['title']} (status: {task['status']})",
            metadata={"task": json.dumps(task)},
        )

    def _do_list(self, data: dict[str, Any]) -> ToolResult:
        todos = data.get("todos", [])
        if not todos:
            return ToolResult(output="No tasks found.")

        lines = [f"Tasks ({len(todos)} total):\n"]
        for task in todos:
            status_icon = {
                "pending": "[ ]",
                "in_progress": "[~]",
                "completed": "[x]",
            }.get(task["status"], "[?]")
            lines.append(f"{status_icon} [{task['id']}] {task['title']} ({task['status']})")
            if task.get("description"):
                lines.append(f"    {task['description']}")

        return ToolResult(output="\n".join(lines))

    def _do_update(
        self, data: dict[str, Any], arguments: TodoWriteInput, path: Path
    ) -> ToolResult:
        task_id = arguments.task_id
        if not task_id:
            return ToolResult(
                output="Error: 'task_id' is required for update action.",
                is_error=True,
            )

        for task in data.get("todos", []):
            if task["id"] == task_id:
                if arguments.status:
                    task["status"] = arguments.status
                if arguments.title is not None:
                    task["title"] = arguments.title.strip()
                if arguments.description is not None:
                    task["description"] = arguments.description.strip()
                task["updated_at"] = self._now()
                self._save_todos(path, data)
                return ToolResult(
                    output=f"Updated task [{task_id}]: status={task['status']}, title={task['title']}"
                )

        return ToolResult(
            output=f"Error: Task '{task_id}' not found.",
            is_error=True,
        )

    def _do_delete(
        self, data: dict[str, Any], arguments: TodoWriteInput, path: Path
    ) -> ToolResult:
        task_id = arguments.task_id
        if not task_id:
            return ToolResult(
                output="Error: 'task_id' is required for delete action.",
                is_error=True,
            )

        original_len = len(data.get("todos", []))
        data["todos"] = [t for t in data.get("todos", []) if t["id"] != task_id]

        if len(data["todos"]) == original_len:
            return ToolResult(
                output=f"Error: Task '{task_id}' not found.",
                is_error=True,
            )

        self._save_todos(path, data)
        return ToolResult(output=f"Deleted task [{task_id}].")

    def _do_clear_completed(
        self, data: dict[str, Any], path: Path
    ) -> ToolResult:
        original_len = len(data.get("todos", []))
        data["todos"] = [t for t in data.get("todos", []) if t["status"] != "completed"]
        removed = original_len - len(data["todos"])
        self._save_todos(path, data)
        return ToolResult(output=f"Cleared {removed} completed task(s). {len(data['todos'])} task(s) remaining.")
