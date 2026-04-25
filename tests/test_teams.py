"""Tests for team orchestration."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from myagent.engine.stream_events import AssistantTextDelta
from myagent.tasks.models import SubTask, Task, TaskStatus
from myagent.teams.orchestrator import TeamOrchestrator


class FakeEngine:
    """最小可执行假引擎。"""

    async def submit_message(self, message: str):
        yield AssistantTextDelta(text=f"done: {message}")


class FakeEngineManager:
    """为团队执行提供假引擎。"""

    def create_engine(self, agent_name: str):
        return FakeEngine()


@pytest.mark.asyncio
async def test_team_orchestrator_executes_task_and_updates_team_status():
    """团队编排执行后应推进任务与成员状态。"""
    task_engine = SimpleNamespace(engine_manager=FakeEngineManager())
    orchestrator = TeamOrchestrator(task_engine)
    task = Task(
        title="实现 Phase 4",
        description="让任务与团队流可见",
        subtasks=[SubTask(description="执行第一个子任务", agent="worker")],
    )

    events = [event async for event in orchestrator.execute_with_team(task)]

    assert events[0]["type"] == "team_start"
    assert any(event["type"] == "member_assigned" for event in events)
    assert any(event["type"] == "member_complete" for event in events)
    assert events[-1]["type"] == "team_complete"
    assert any(event["type"] == "member_assigned" for event in task.events)
    assert any(event["type"] == "member_complete" for event in task.events)
    assert task.status == TaskStatus.EXECUTED
    assert task.subtasks[0].status == TaskStatus.DONE
    assert orchestrator.get_team_status()["total_completed"] >= 1
