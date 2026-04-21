"""Swarm coordinator for multi-agent collaboration."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from myagent.engine.query_engine import QueryEngine
from myagent.tools.registry import ToolRegistry


class TaskStatus(Enum):
    """Status of a swarm task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SwarmTask:
    """A task in the swarm."""

    id: str
    description: str
    assigned_agent: str | None
    status: TaskStatus = TaskStatus.PENDING
    result: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "assigned_agent": self.assigned_agent,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
        }


class SwarmCoordinator:
    """Coordinates multiple agents working on tasks."""

    def __init__(self, llm_client: Any | None = None) -> None:
        self._tasks: dict[str, SwarmTask] = {}
        self._agents: dict[str, str] = {}
        self.llm_client = llm_client

    def register_agent(self, name: str, system_prompt: str) -> None:
        """Register an agent with its system prompt."""
        self._agents[name] = system_prompt

    def create_task(
        self,
        description: str,
        assigned_agent: str | None = None,
    ) -> SwarmTask:
        """Create a new task."""
        task = SwarmTask(
            id=str(uuid.uuid4())[:8],
            description=description,
            assigned_agent=assigned_agent,
        )
        self._tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> SwarmTask | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self, status: TaskStatus | None = None) -> list[SwarmTask]:
        """List all tasks, optionally filtered by status."""
        tasks = list(self._tasks.values())
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    async def execute_task(self, task_id: str) -> str:
        """Execute a single task using its assigned agent."""
        task = self._tasks.get(task_id)
        if task is None:
            return f"Error: Task '{task_id}' not found."

        if task.assigned_agent is None:
            return f"Error: Task '{task_id}' has no assigned agent."

        agent_prompt = self._agents.get(task.assigned_agent)
        if agent_prompt is None:
            return f"Error: Agent '{task.assigned_agent}' not registered."

        task.status = TaskStatus.IN_PROGRESS

        try:
            tool_registry = ToolRegistry()
            engine = QueryEngine(
                tool_registry=tool_registry,
                system_prompt=agent_prompt,
                llm_client=self.llm_client,
            )

            output_parts: list[str] = []
            async for event in engine.submit_message(task.description):
                if hasattr(event, "text"):
                    output_parts.append(event.text)

            result = "".join(output_parts) or "Task completed with no output."
            task.result = result
            task.status = TaskStatus.COMPLETED
            return result

        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            return f"Error executing task '{task_id}': {e}"

    async def execute_all(self) -> dict[str, str]:
        """Execute all pending tasks in parallel."""
        pending = self.list_tasks(status=TaskStatus.PENDING)
        results: dict[str, str] = {}

        async def run_task(task: SwarmTask) -> None:
            results[task.id] = await self.execute_task(task.id)

        await asyncio.gather(*(run_task(t) for t in pending))
        return results

    async def execute_sequential(self) -> dict[str, str]:
        """Execute all pending tasks sequentially."""
        pending = self.list_tasks(status=TaskStatus.PENDING)
        results: dict[str, str] = {}

        for task in pending:
            results[task.id] = await self.execute_task(task.id)

        return results

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all tasks."""
        tasks = list(self._tasks.values())
        return {
            "total": len(tasks),
            "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
            "in_progress": sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS),
            "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            "agents": list(self._agents.keys()),
        }
