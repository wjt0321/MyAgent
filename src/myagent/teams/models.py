"""Team models for multi-agent collaboration."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TeamRole(Enum):
    """Predefined team roles."""
    LEAD = "lead"              # Team lead, coordinates and decides
    PLANNER = "planner"        # Creates plans and strategies
    EXECUTOR = "executor"      # Implements and executes
    REVIEWER = "reviewer"      # Reviews code and quality
    EXPLORER = "explorer"      # Investigates and researches
    SPECIALIST = "specialist"  # Domain expert


@dataclass
class TeamMember:
    """A member of an agent team."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""             # Agent name (e.g., "worker", "reviewer")
    role: TeamRole = TeamRole.EXECUTOR
    description: str = ""      # Role description
    status: str = "idle"       # idle | busy | offline
    current_task: str | None = None
    completed_tasks: int = 0
    failed_tasks: int = 0
    avatar_color: str = "#6366f1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "description": self.description,
            "status": self.status,
            "current_task": self.current_task,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "avatar_color": self.avatar_color,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TeamMember:
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", ""),
            role=TeamRole(data.get("role", "executor")),
            description=data.get("description", ""),
            status=data.get("status", "idle"),
            current_task=data.get("current_task"),
            completed_tasks=data.get("completed_tasks", 0),
            failed_tasks=data.get("failed_tasks", 0),
            avatar_color=data.get("avatar_color", "#6366f1"),
        )


@dataclass
class Team:
    """A team of agents working together."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Default Team"
    description: str = ""
    members: list[TeamMember] = field(default_factory=list)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "members": [m.to_dict() for m in self.members],
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Team:
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", "Default Team"),
            description=data.get("description", ""),
            members=[TeamMember.from_dict(m) for m in data.get("members", [])],
            active=data.get("active", True),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
        )

    def get_member(self, name: str) -> TeamMember | None:
        """Get a member by agent name."""
        for member in self.members:
            if member.name == name:
                return member
        return None

    def get_members_by_role(self, role: TeamRole) -> list[TeamMember]:
        """Get all members with a specific role."""
        return [m for m in self.members if m.role == role]

    def get_available_member(self, role: TeamRole | None = None) -> TeamMember | None:
        """Get an available (idle) member, optionally filtered by role."""
        candidates = self.members if role is None else self.get_members_by_role(role)
        for member in candidates:
            if member.status == "idle":
                return member
        return None

    def update_member_status(self, name: str, status: str, task: str | None = None) -> None:
        """Update a member's status."""
        member = self.get_member(name)
        if member:
            member.status = status
            member.current_task = task
            self.updated_at = datetime.now()

    @classmethod
    def create_default_team(cls) -> Team:
        """Create the default agent team."""
        return cls(
            name="Core Team",
            description="Default multi-agent team for general tasks",
            members=[
                TeamMember(
                    name="plan",
                    role=TeamRole.PLANNER,
                    description="Creates detailed execution plans",
                    avatar_color="#f59e0b",
                ),
                TeamMember(
                    name="explore",
                    role=TeamRole.EXPLORER,
                    description="Investigates codebase and gathers context",
                    avatar_color="#10b981",
                ),
                TeamMember(
                    name="worker",
                    role=TeamRole.EXECUTOR,
                    description="Implements features and writes code",
                    avatar_color="#6366f1",
                ),
                TeamMember(
                    name="reviewer",
                    role=TeamRole.REVIEWER,
                    description="Reviews code quality and correctness",
                    avatar_color="#ec4899",
                ),
            ],
        )
