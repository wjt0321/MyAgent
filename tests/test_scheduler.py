"""Tests for TaskScheduler."""

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from myagent.scheduler.core import ScheduledTask, TaskScheduler


class TestScheduledTask:
    def test_task_creation(self):
        task = ScheduledTask(
            id="task-1",
            name="Daily backup",
            cron="0 0 * * *",
            action=lambda: "done",
        )
        assert task.id == "task-1"
        assert task.name == "Daily backup"
        assert task.cron == "0 0 * * *"
        assert task.enabled is True

    def test_task_next_run_delay(self):
        task = ScheduledTask(
            id="task-1",
            name="Soon",
            delay_seconds=1,
            action=lambda: "done",
        )
        assert task.delay_seconds == 1
        assert task.cron is None


class TestTaskScheduler:
    def test_scheduler_creation(self):
        scheduler = TaskScheduler()
        assert scheduler._tasks == {}
        assert scheduler._running is False

    def test_add_task(self):
        scheduler = TaskScheduler()
        task = scheduler.add_task(
            name="Test task",
            delay_seconds=10,
            action=lambda: "done",
        )
        assert task.id in scheduler._tasks
        assert task.name == "Test task"

    def test_add_cron_task(self):
        scheduler = TaskScheduler()
        task = scheduler.add_task(
            name="Daily",
            cron="0 9 * * *",
            action=lambda: "morning",
        )
        assert task.cron == "0 9 * * *"

    def test_remove_task(self):
        scheduler = TaskScheduler()
        task = scheduler.add_task(name="Temp", delay_seconds=5, action=lambda: None)
        scheduler.remove_task(task.id)
        assert task.id not in scheduler._tasks

    def test_get_task(self):
        scheduler = TaskScheduler()
        task = scheduler.add_task(name="Test", delay_seconds=5, action=lambda: None)
        retrieved = scheduler.get_task(task.id)
        assert retrieved is task

    def test_get_task_not_found(self):
        scheduler = TaskScheduler()
        assert scheduler.get_task("nonexistent") is None

    def test_list_tasks(self):
        scheduler = TaskScheduler()
        scheduler.add_task(name="A", delay_seconds=5, action=lambda: None)
        scheduler.add_task(name="B", delay_seconds=10, action=lambda: None)
        assert len(scheduler.list_tasks()) == 2

    def test_enable_disable_task(self):
        scheduler = TaskScheduler()
        task = scheduler.add_task(name="Test", delay_seconds=5, action=lambda: None)

        scheduler.disable_task(task.id)
        assert task.enabled is False

        scheduler.enable_task(task.id)
        assert task.enabled is True

    @pytest.mark.asyncio
    async def test_run_task_once(self):
        scheduler = TaskScheduler()
        called = []

        async def async_action():
            called.append(1)

        task = scheduler.add_task(name="Once", delay_seconds=0, action=async_action)

        await scheduler._run_task(task)

        assert len(called) == 1
        assert task.last_run is not None

    @pytest.mark.asyncio
    async def test_run_sync_action(self):
        scheduler = TaskScheduler()
        called = []

        def sync_action():
            called.append(1)

        task = scheduler.add_task(name="Sync", delay_seconds=0, action=sync_action)

        await scheduler._run_task(task)

        assert len(called) == 1

    @pytest.mark.asyncio
    async def test_run_task_error(self):
        scheduler = TaskScheduler()

        async def bad_action():
            raise ValueError("Oops")

        task = scheduler.add_task(name="Bad", delay_seconds=0, action=bad_action)

        await scheduler._run_task(task)

        assert task.last_error == "Oops"

    @pytest.mark.asyncio
    async def test_start_stop(self):
        scheduler = TaskScheduler()

        async def action():
            pass

        scheduler.add_task(name="Test", delay_seconds=3600, action=action)

        await scheduler.start()
        assert scheduler._running is True

        await scheduler.stop()
        assert scheduler._running is False

    def test_parse_cron_simple(self):
        scheduler = TaskScheduler()
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        next_run = scheduler._parse_cron("0 14 * * *", now)
        assert next_run.hour == 14
        assert next_run.minute == 0

    def test_parse_delay(self):
        scheduler = TaskScheduler()
        now = datetime.now(timezone.utc)

        task = ScheduledTask(id="t", name="T", delay_seconds=60, action=lambda: None)
        next_run = scheduler._get_next_run(task, now)

        expected = now + timedelta(seconds=60)
        assert abs((next_run - expected).total_seconds()) < 1
