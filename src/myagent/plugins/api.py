"""Plugin API for MyAgent."""

from __future__ import annotations

from typing import Any, Callable

from myagent.plugins.hooks import HookCallback, HookPoint
from myagent.tools.base import BaseTool


class PluginAPI:
    """API exposed to plugins for registration."""

    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id
        self.tools: list[BaseTool] = []
        self.agents: dict[str, str] = {}
        self.hooks: dict[HookPoint, HookCallback] = {}
        self.metadata: dict[str, Any] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool provided by this plugin."""
        self.tools.append(tool)

    def register_agent(self, name: str, system_prompt: str) -> None:
        """Register an agent definition provided by this plugin."""
        self.agents[name] = system_prompt

    def register_hook(
        self,
        hook_point: HookPoint | str,
        callback: HookCallback
    ) -> None:
        """Register a hook callback for an execution point.

        Args:
            hook_point: The execution point to hook into (enum or string).
            callback: The function to call when the hook is triggered.
        """
        if isinstance(hook_point, str):
            try:
                hook_point = HookPoint(hook_point)
            except ValueError:
                pass

        if isinstance(hook_point, HookPoint):
            self.hooks[hook_point] = callback
        else:
            # Legacy string-based hook support
            pass
