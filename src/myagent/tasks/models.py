"""Task models for Plan -> Execute -> Review workflow."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(Enum):
    """Task lifecycle states."""
    PENDING = "pending"           # Created, waiting to start
    PLANNING = "planning"         # Agent is creating plan
    PLANNED = "planned"           # Plan created, waiting for approval
    EXECUTING = "executing"       # Executing the plan
    EXECUTED = "executed"         # Execution complete, waiting for review
    REVIEWING = "reviewing"       # Reviewing results
    DONE = "done"                 # Review passed, task complete
    FAILED = "failed"             # Execution or review failed
    CANCELLED = "cancelled"       # User cancelled


@dataclass
class SubTask:
    """A single step in a plan."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    agent: str = "worker"         # Which agent should execute this
    result: str = ""              # Execution result
    error: str | None = None      # Error message if failed
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "agent": self.agent,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SubTask:
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "pending")),
            agent=data.get("agent", "worker"),
            result=data.get("result", ""),
            error=data.get("error"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )


@dataclass
class TaskResult:
    """Result of task execution and review."""
    success: bool = False
    summary: str = ""             # Brief summary of what was done
    deliverables: list[str] = field(default_factory=list)  # Files/changes produced
    issues: list[str] = field(default_factory=list)         # Issues found
    suggestions: list[str] = field(default_factory=list)    # Improvement suggestions

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "summary": self.summary,
            "deliverables": self.deliverables,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskResult:
        return cls(
            success=data.get("success", False),
            summary=data.get("summary", ""),
            deliverables=data.get("deliverables", []),
            issues=data.get("issues", []),
            suggestions=data.get("suggestions", []),
        )


@dataclass
class Task:
    """A task with Plan -> Execute -> Review lifecycle."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""               # Short task title
    description: str = ""         # Full task description
    status: TaskStatus = TaskStatus.PENDING
    subtasks: list[SubTask] = field(default_factory=list)
    result: TaskResult | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    plan_approved: bool = False   # User approved the plan
    review_passed: bool = False   # Review passed
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    project: str = "default"      # Associated project

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "subtasks": [s.to_dict() for s in self.subtasks],
            "result": self.result.to_dict() if self.result else None,
            "events": self.events,
            "plan_approved": self.plan_approved,
            "review_passed": self.review_passed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "project": self.project,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "pending")),
            subtasks=[SubTask.from_dict(s) for s in data.get("subtasks", [])],
            result=TaskResult.from_dict(data["result"]) if data.get("result") else None,
            events=data.get("events", []),
            plan_approved=data.get("plan_approved", False),
            review_passed=data.get("review_passed", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            project=data.get("project", "default"),
        )

    def update_status(self, status: TaskStatus) -> None:
        """Update task status and timestamp."""
        self.status = status
        self.updated_at = datetime.now()

    def add_event(
        self,
        event_type: str,
        message: str,
        *,
        member: str | None = None,
        subtask_id: str | None = None,
        status: str | None = None,
    ) -> None:
        """Append a structured task timeline event."""
        event = {
            "type": event_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        if member is not None:
            event["member"] = member
        if subtask_id is not None:
            event["subtask_id"] = subtask_id
        if status is not None:
            event["status"] = status
        self.events.append(event)

    def get_progress(self) -> tuple[int, int]:
        """Return (completed, total) subtask counts."""
        total = len(self.subtasks)
        completed = sum(
            1 for s in self.subtasks
            if s.status in (TaskStatus.DONE, TaskStatus.FAILED)
        )
        return completed, total

    def is_complete(self) -> bool:
        """Check if task is fully complete."""
        return self.status in (TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELLED)
