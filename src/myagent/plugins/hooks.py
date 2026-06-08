"""Plugin hook system for MyAgent.

Provides a centralized hook system for plugins to respond to events.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class HookPoint(Enum):
    """Points in the execution flow where plugins can hook in."""

    SESSION_START = "session_start"
    """Triggered when a new chat session starts."""

    SESSION_END = "session_end"
    """Triggered when a chat session ends."""

    USER_MESSAGE = "user_message"
    """Triggered when a user sends a message."""

    ASSISTANT_MESSAGE = "assistant_message"
    """Triggered when the assistant sends a message."""

    TOOL_BEFORE = "tool_before"
    """Triggered before a tool is executed."""

    TOOL_AFTER = "tool_after"
    """Triggered after a tool is executed."""

    ASSISTANT_COMPLETE = "assistant_complete"
    """Triggered when the assistant completes a turn."""


@dataclass
class HookContext:
    """Context passed to hook callbacks."""

    session_id: str
    """ID of the current session."""

    agent: str = "general"
    """Name of the current agent."""

    user_id: str = "default"
    """ID of the current user."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional plugin-specific metadata."""


HookCallback = Callable[[HookContext], Any]
"""Type alias for hook callbacks (sync or async)."""


class HookRegistry:
    """Central registry for plugin hooks.

    Allows plugins to register callbacks to be triggered at specific execution points.
    """

    def __init__(self) -> None:
        self._hooks: dict[HookPoint, list[tuple[str, HookCallback]]] = {}
        """Mapping from hook point to list of (plugin_id, callback) tuples."""

    def register(
        self,
        hook_point: HookPoint,
        callback: HookCallback,
        plugin_id: str = "unknown"
    ) -> None:
        """Register a callback for a specific hook point.

        Args:
            hook_point: The point in execution to hook into.
            callback: The function to call when the hook is triggered.
            plugin_id: ID of the plugin registering the hook (for debugging).
        """
        if hook_point not in self._hooks:
            self._hooks[hook_point] = []
        self._hooks[hook_point].append((plugin_id, callback))
        logger.debug(f"Plugin '{plugin_id}' registered hook for {hook_point}")

    def unregister(
        self,
        hook_point: HookPoint | None = None,
        plugin_id: str | None = None
    ) -> None:
        """Unregister hooks.

        Args:
            hook_point: Specific hook point to unregister from (all if None).
            plugin_id: Specific plugin to unregister (all if None).
        """
        points = [hook_point] if hook_point else list(self._hooks.keys())

        for point in points:
            if point in self._hooks:
                if plugin_id:
                    self._hooks[point] = [
                        (pid, cb) for pid, cb in self._hooks[point] if pid != plugin_id
                    ]
                else:
                    self._hooks[point] = []
                if not self._hooks[point]:
                    del self._hooks[point]

    async def trigger(
        self,
        hook_point: HookPoint,
        context: HookContext
    ) -> list[Any]:
        """Trigger all callbacks for a hook point.

        Args:
            hook_point: The hook point to trigger.
            context: The context to pass to callbacks.

        Returns:
            List of results from all callbacks (synchronous results first).
        """
        results: list[Any] = []

        if hook_point not in self._hooks:
            return results

        callbacks = self._hooks[hook_point]
        logger.debug(f"Triggering {len(callbacks)} callbacks for {hook_point}")

        for plugin_id, callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    result = await callback(context)
                else:
                    result = callback(context)
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Hook callback from plugin '{plugin_id}' failed for {hook_point}: {e}",
                    exc_info=True
                )

        return results

    def list_hooks(self) -> dict[HookPoint, list[str]]:
        """List all registered hooks by plugin ID.

        Returns:
            Dictionary mapping hook points to lists of plugin IDs.
        """
        result: dict[HookPoint, list[str]] = {}
        for point, callbacks in self._hooks.items():
            result[point] = [pid for pid, _ in callbacks]
        return result
