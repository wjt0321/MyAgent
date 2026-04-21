"""Task scheduler for MyAgent."""

from __future__ import annotations

import asyncio
import inspect
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable


@dataclass
class ScheduledTask:
    """A scheduled task definition."""

    id: str
    name: str
    action: Callable[..., Any]
    cron: str | None = None
    delay_seconds: int | None = None
    enabled: bool = True
    last_run: datetime | None = None
    last_error: str | None = None
    run_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TaskScheduler:
    """Lightweight task scheduler for delayed and periodic execution."""

    def __init__(self) -> None:
        self._tasks: dict[str, ScheduledTask] = {}
        self._running = False
        self._task: asyncio.Task[Any] | None = None

    def add_task(
        self,
        name: str,
        action: Callable[..., Any],
        cron: str | None = None,
        delay_seconds: int | None = None,
    ) -> ScheduledTask:
        """Add a new scheduled task."""
        task = ScheduledTask(
            id=str(uuid.uuid4())[:8],
            name=name,
            action=action,
            cron=cron,
            delay_seconds=delay_seconds,
        )
        self._tasks[task.id] = task
        return task

    def remove_task(self, task_id: str) -> None:
        """Remove a scheduled task."""
        self._tasks.pop(task_id, None)

    def get_task(self, task_id: str) -> ScheduledTask | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self) -> list[ScheduledTask]:
        """List all scheduled tasks."""
        return list(self._tasks.values())

    def enable_task(self, task_id: str) -> None:
        """Enable a task."""
        task = self._tasks.get(task_id)
        if task:
            task.enabled = True

    def disable_task(self, task_id: str) -> None:
        """Disable a task."""
        task = self._tasks.get(task_id)
        if task:
            task.enabled = False

    async def start(self) -> None:
        """Start the scheduler loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            now = datetime.now(timezone.utc)

            for task in list(self._tasks.values()):
                if not task.enabled:
                    continue

                next_run = self._get_next_run(task, now)
                if next_run and next_run <= now:
                    await self._run_task(task)

            await asyncio.sleep(1)

    async def _run_task(self, task: ScheduledTask) -> None:
        """Execute a single task."""
        try:
            if inspect.iscoroutinefunction(task.action):
                await task.action()
            else:
                task.action()

            task.last_run = datetime.now(timezone.utc)
            task.last_error = None
            task.run_count += 1

        except Exception as e:
            task.last_error = str(e)

    def _get_next_run(self, task: ScheduledTask, now: datetime) -> datetime | None:
        """Calculate the next run time for a task."""
        if task.cron:
            return self._parse_cron(task.cron, now)
        elif task.delay_seconds is not None:
            base = task.last_run or task.created_at
            return base + timedelta(seconds=task.delay_seconds)
        return None

    def _parse_cron(self, cron: str, now: datetime) -> datetime | None:
        """Simple cron parser (supports 'M H * * *' format only)."""
        parts = cron.split()
        if len(parts) != 5:
            return None

        try:
            minute = int(parts[0])
            hour = int(parts[1])
        except ValueError:
            return None

        candidate = now.replace(minute=minute, second=0, microsecond=0)
        if parts[1] != "*":
            candidate = candidate.replace(hour=hour)

        if candidate <= now:
            candidate = candidate + timedelta(days=1)

        return candidate
