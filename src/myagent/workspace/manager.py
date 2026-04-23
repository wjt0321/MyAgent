"""Workspace directory management.

Handles creation, validation, and navigation of the MyAgent workspace.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


DEFAULT_WORKSPACE_NAME = ".myagent"


def get_workspace_dir() -> Path:
    """Return the MyAgent workspace directory."""
    home = os.getenv("MYAGENT_HOME")
    if home:
        return Path(home)
    return Path.home() / DEFAULT_WORKSPACE_NAME


def get_memory_dir(workspace: str | Path | None = None) -> Path:
    """Return the memory directory for a workspace."""
    if workspace is None:
        workspace = get_workspace_dir()
    return Path(workspace) / "memory"


def get_projects_dir(workspace: str | Path | None = None) -> Path:
    """Return the projects directory."""
    if workspace is None:
        workspace = get_workspace_dir()
    return Path(workspace) / "projects"


def get_sessions_dir(workspace: str | Path | None = None) -> Path:
    """Return the sessions directory."""
    if workspace is None:
        workspace = get_workspace_dir()
    return Path(workspace) / "sessions"


def get_skills_dir(workspace: str | Path | None = None) -> Path:
    """Return the skills directory."""
    if workspace is None:
        workspace = get_workspace_dir()
    return Path(workspace) / "skills"


def get_logs_dir(workspace: str | Path | None = None) -> Path:
    """Return the logs directory."""
    if workspace is None:
        workspace = get_workspace_dir()
    return Path(workspace) / "logs"


def ensure_workspace(workspace: str | Path | None = None) -> Path:
    """Create workspace directories if they don't exist.

    Returns the workspace path.
    """
    ws = Path(workspace) if workspace else get_workspace_dir()

    dirs = [
        ws,
        ws / "memory",
        ws / "projects",
        ws / "projects" / "default",
        ws / "projects" / "default" / ".myagent",
        ws / "projects" / "default" / ".myagent" / "memory",
        ws / "projects" / "default" / ".myagent" / "agents",
        ws / "projects" / "default" / ".myagent" / "tasks",
        ws / "sessions",
        ws / "logs",
        ws / "skills",
        ws / "workspace",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    return ws


class WorkspaceManager:
    """Manages the MyAgent workspace lifecycle."""

    def __init__(self, workspace_dir: str | Path | None = None) -> None:
        self.workspace_dir = Path(workspace_dir) if workspace_dir else get_workspace_dir()
        self.memory_dir = get_memory_dir(self.workspace_dir)
        self.projects_dir = get_projects_dir(self.workspace_dir)
        self.sessions_dir = get_sessions_dir(self.workspace_dir)
        self.skills_dir = get_skills_dir(self.workspace_dir)
        self.logs_dir = get_logs_dir(self.workspace_dir)

    def ensure(self) -> Path:
        """Ensure workspace exists."""
        return ensure_workspace(self.workspace_dir)

    def exists(self) -> bool:
        """Check if workspace is initialized."""
        return (self.workspace_dir / "soul.md").exists()

    def get_project_dir(self, name: str = "default") -> Path:
        """Get a project directory."""
        return self.projects_dir / name

    def ensure_project(self, name: str = "default") -> Path:
        """Ensure a project directory exists."""
        project_dir = self.get_project_dir(name)
        dirs = [
            project_dir,
            project_dir / ".myagent",
            project_dir / ".myagent" / "memory",
            project_dir / ".myagent" / "agents",
            project_dir / ".myagent" / "tasks",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        return project_dir

    def list_projects(self) -> list[str]:
        """List all project names."""
        if not self.projects_dir.exists():
            return []
        return [p.name for p in self.projects_dir.iterdir() if p.is_dir()]

    def get_memory_files(self) -> list[Path]:
        """List all memory markdown files."""
        if not self.memory_dir.exists():
            return []
        return sorted(
            path for path in self.memory_dir.glob("*.md")
            if path.name != "MEMORY.md"
        )

    def get_memory_index_path(self) -> Path:
        """Get the memory index file path."""
        return self.memory_dir / "MEMORY.md"

    def read_soul(self) -> str | None:
        """Read the soul.md file."""
        path = self.workspace_dir / "soul.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def read_user_profile(self) -> str | None:
        """Read the user.md file."""
        path = self.workspace_dir / "user.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def read_identity(self) -> str | None:
        """Read the identity.md file."""
        path = self.workspace_dir / "identity.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None
