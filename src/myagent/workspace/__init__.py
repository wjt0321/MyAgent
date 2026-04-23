"""MyAgent Workspace module.

Manages the workspace directory structure, templates, and project lifecycle.
Inspired by OpenHarness (ohmo) and Claude Code's memdir system.
"""

from myagent.workspace.manager import (
    WorkspaceManager,
    get_workspace_dir,
    get_memory_dir,
    get_projects_dir,
    get_sessions_dir,
    ensure_workspace,
)
from myagent.workspace.templates import render_template

__all__ = [
    "WorkspaceManager",
    "get_workspace_dir",
    "get_memory_dir",
    "get_projects_dir",
    "get_sessions_dir",
    "ensure_workspace",
    "render_template",
]
