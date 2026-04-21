"""Plugin API for MyAgent."""

from __future__ import annotations

from typing import Any, Callable

from myagent.tools.base import BaseTool


class PluginAPI:
    """API exposed to plugins for registration."""

    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id
        self.tools: list[BaseTool] = []
        self.agents: dict[str, str] = {}
        self.hooks: dict[str, Callable[..., Any]] = {}
        self.metadata: dict[str, Any] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool provided by this plugin."""
        self.tools.append(tool)

    def register_agent(self, name: str, system_prompt: str) -> None:
        """Register an agent definition provided by this plugin."""
        self.agents[name] = system_prompt

    def register_hook(self, event: str, handler: Callable[..., Any]) -> None:
        """Register a lifecycle hook handler."""
        self.hooks[event] = handler
