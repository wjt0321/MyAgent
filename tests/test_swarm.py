"""Tests for Swarm multi-agent collaboration."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from myagent.swarm.coordinator import SwarmCoordinator, SwarmTask, TaskStatus


class TestSwarmTask:
    def test_task_creation(self):
        task = SwarmTask(
            id="task-1",
            description="Analyze code",
            assigned_agent="code-analyzer",
        )
        assert task.id == "task-1"
        assert task.description == "Analyze code"
        assert task.status == TaskStatus.PENDING
        assert task.result is None

    def test_task_to_dict(self):
        task = SwarmTask(
            id="task-1",
            description="Test",
            assigned_agent="agent-a",
            status=TaskStatus.COMPLETED,
            result="Done",
        )
        data = task.to_dict()
        assert data["id"] == "task-1"
        assert data["status"] == "completed"
        assert data["result"] == "Done"


class TestSwarmCoordinator:
    def test_coordinator_creation(self):
        coord = SwarmCoordinator()
        assert coord._tasks == {}
        assert coord._agents == {}

    def test_register_agent(self):
        coord = SwarmCoordinator()
        coord.register_agent("analyzer", "You analyze code.")
        assert "analyzer" in coord._agents
        assert coord._agents["analyzer"] == "You analyze code."

    def test_create_task(self):
        coord = SwarmCoordinator()
        coord.register_agent("worker", "You work.")
        task = coord.create_task("Do something", assigned_agent="worker")

        assert task.id in coord._tasks
        assert task.description == "Do something"
        assert task.assigned_agent == "worker"
        assert task.status == TaskStatus.PENDING

    def test_create_task_without_agent(self):
        coord = SwarmCoordinator()
        task = coord.create_task("Do something")

        assert task.assigned_agent is None

    def test_get_task(self):
        coord = SwarmCoordinator()
        created = coord.create_task("Test", assigned_agent="a")
        retrieved = coord.get_task(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_task_not_found(self):
        coord = SwarmCoordinator()
        assert coord.get_task("nonexistent") is None

    def test_list_tasks(self):
        coord = SwarmCoordinator()
        coord.create_task("Task 1", assigned_agent="a")
        coord.create_task("Task 2", assigned_agent="b")

        tasks = coord.list_tasks()
        assert len(tasks) == 2

    def test_list_tasks_by_status(self):
        coord = SwarmCoordinator()
        t1 = coord.create_task("Task 1", assigned_agent="a")
        t2 = coord.create_task("Task 2", assigned_agent="b")
        t2.status = TaskStatus.COMPLETED

        pending = coord.list_tasks(status=TaskStatus.PENDING)
        completed = coord.list_tasks(status=TaskStatus.COMPLETED)

        assert len(pending) == 1
        assert len(completed) == 1

    @pytest.mark.asyncio
    async def test_execute_task(self):
        coord = SwarmCoordinator()
        coord.register_agent("worker", "You are a worker.")
        task = coord.create_task("Process data", assigned_agent="worker")

        mock_engine = MagicMock()
        mock_event = MagicMock()
        mock_event.text = "Processed successfully"

        async def async_iter():
            yield mock_event

        mock_engine.submit_message.return_value = async_iter()

        with patch("myagent.swarm.coordinator.QueryEngine", return_value=mock_engine):
            with patch("myagent.swarm.coordinator.ToolRegistry"):
                result = await coord.execute_task(task.id)

        assert result == "Processed successfully"
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "Processed successfully"

    @pytest.mark.asyncio
    async def test_execute_task_not_found(self):
        coord = SwarmCoordinator()
        result = await coord.execute_task("nonexistent")
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_task_no_agent(self):
        coord = SwarmCoordinator()
        task = coord.create_task("Orphan task")
        result = await coord.execute_task(task.id)
        assert "no assigned agent" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_task_engine_error(self):
        coord = SwarmCoordinator()
        coord.register_agent("worker", "You are a worker.")
        task = coord.create_task("Fail task", assigned_agent="worker")

        mock_engine = MagicMock()
        mock_engine.submit_message.side_effect = Exception("Engine crashed")

        with patch("myagent.swarm.coordinator.QueryEngine", return_value=mock_engine):
            with patch("myagent.swarm.coordinator.ToolRegistry"):
                result = await coord.execute_task(task.id)

        assert "error" in result.lower()
        assert task.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_all(self):
        coord = SwarmCoordinator()
        coord.register_agent("a", "Agent A")
        coord.register_agent("b", "Agent B")

        coord.create_task("Task 1", assigned_agent="a")
        coord.create_task("Task 2", assigned_agent="b")

        mock_engine = MagicMock()
        mock_event = MagicMock()
        mock_event.text = "Done"

        async def async_iter():
            yield mock_event

        mock_engine.submit_message.side_effect = lambda *a, **k: async_iter()

        with patch("myagent.swarm.coordinator.QueryEngine", return_value=mock_engine):
            with patch("myagent.swarm.coordinator.ToolRegistry"):
                results = await coord.execute_all()

        assert len(results) == 2
        assert all(r == "Done" for r in results.values())

    @pytest.mark.asyncio
    async def test_execute_sequential(self):
        coord = SwarmCoordinator()
        coord.register_agent("a", "Agent A")

        coord.create_task("Step 1", assigned_agent="a")
        coord.create_task("Step 2", assigned_agent="a")

        mock_engine = MagicMock()
        mock_event = MagicMock()
        mock_event.text = "Step done"

        async def async_iter():
            yield mock_event

        mock_engine.submit_message.return_value = async_iter()

        with patch("myagent.swarm.coordinator.QueryEngine", return_value=mock_engine):
            with patch("myagent.swarm.coordinator.ToolRegistry"):
                results = await coord.execute_sequential()

        assert len(results) == 2

    def test_get_summary(self):
        coord = SwarmCoordinator()
        coord.register_agent("a", "Agent A")
        t1 = coord.create_task("T1", assigned_agent="a")
        t1.status = TaskStatus.COMPLETED
        t2 = coord.create_task("T2", assigned_agent="a")
        t2.status = TaskStatus.FAILED
        coord.create_task("T3", assigned_agent="a")

        summary = coord.get_summary()
        assert summary["total"] == 3
        assert summary["completed"] == 1
        assert summary["failed"] == 1
        assert summary["pending"] == 1
