"""QueryEngine manager for Web UI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from myagent.agents.loader import AgentLoader
from myagent.cost.tracker import CostTracker
from myagent.engine.query_engine import QueryEngine
from myagent.engine.stream_events import (
    AssistantTextDelta,
    AssistantTurnComplete,
    ErrorEvent,
    PermissionRequestEvent,
    PermissionResultEvent,
    ToolExecutionCompleted,
    ToolExecutionStarted,
)
from myagent.llm.providers.anthropic import AnthropicProvider
from myagent.memory.collection import MemoryCollector
from myagent.memory.manager import MemoryManager
from myagent.security.checker import PermissionChecker
from myagent.tools.bash import Bash
from myagent.tools.edit import Edit
from myagent.tools.glob import Glob
from myagent.tools.grep import Grep
from myagent.tools.read import Read
from myagent.tools.registry import ToolRegistry
from myagent.tools.write import Write
from myagent.workspace.manager import get_workspace_dir


def _get_env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def _create_tool_registry(tool_names: list[str] | None = None) -> ToolRegistry:
    all_tools: dict[str, Any] = {
        "Read": Read(),
        "Bash": Bash(),
        "Edit": Edit(),
        "Write": Write(),
        "Glob": Glob(),
        "Grep": Grep(),
    }
    registry = ToolRegistry()
    if tool_names is None:
        for tool in all_tools.values():
            registry.register(tool)
    else:
        for name in tool_names:
            if name in all_tools:
                registry.register(all_tools[name])
    return registry


class WebEngineManager:
    """Manages QueryEngine instances for Web UI sessions."""

    def __init__(self) -> None:
        self._provider: AnthropicProvider | None = None
        self._agent_loader = AgentLoader()
        self._agents = self._agent_loader.load_builtin_agents()
        self._memory_collector: MemoryCollector | None = None
        self._init_provider()
        self._init_memory_collector()

    def _init_memory_collector(self) -> None:
        """Initialize memory collector from workspace."""
        try:
            ws_dir = get_workspace_dir()
            memory_dir = ws_dir / "memory"
            if memory_dir.exists():
                mm = MemoryManager(memory_dir)
                self._memory_collector = MemoryCollector(mm)
        except Exception:
            pass  # Memory collection is optional

    def _init_provider(self) -> None:
        api_key = _get_env("ZHIPU_API_KEY") or _get_env("ANTHROPIC_API_KEY") or _get_env("MYAGENT_API_KEY")
        model = _get_env("ZHIPU_MODEL", "glm-4.7")
        base_url = _get_env("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/anthropic")

        if api_key:
            self._provider = AnthropicProvider(
                api_key=api_key,
                model=model,
                base_url=base_url,
            )

    def is_configured(self) -> bool:
        return self._provider is not None

    def create_engine(self, agent_name: str = "general") -> QueryEngine | None:
        if self._provider is None:
            return None

        agent_def = self._agents.get(agent_name, self._agents.get("general"))
        if agent_def is None:
            return None

        tool_names = agent_def.tools
        if tool_names is not None:
            registry = _create_tool_registry(tool_names)
        else:
            disallowed = agent_def.disallowed_tools or []
            allowed = ["Read", "Bash", "Edit", "Write", "Glob", "Grep"]
            allowed = [t for t in allowed if t not in disallowed]
            registry = _create_tool_registry(allowed)

        permission_mode = agent_def.permission_mode or "default"
        if permission_mode == "dontAsk":
            checker = PermissionChecker()
            checker.approve_once("*", {})
        else:
            checker = PermissionChecker()

        return QueryEngine(
            tool_registry=registry,
            llm_client=self._provider,
            system_prompt=agent_def.system_prompt or "You are a helpful assistant.",
            permission_checker=checker,
            max_turns=agent_def.max_turns or 50,
        )

    async def process_message(
        self,
        engine: QueryEngine,
        message: str,
        send_callback: Any,
    ) -> str:
        """Process a message through QueryEngine and send events via callback.

        Returns the full assistant response text.
        """
        full_response = ""

        async for event in engine.submit_message(message):
            if isinstance(event, AssistantTextDelta):
                await send_callback({"type": "assistant_delta", "text": event.text})
                full_response += event.text

            elif isinstance(event, ToolExecutionStarted):
                await send_callback({
                    "type": "tool_call",
                    "tool_name": event.tool_name,
                    "arguments": event.arguments,
                })

            elif isinstance(event, ToolExecutionCompleted):
                await send_callback({
                    "type": "tool_result",
                    "result": event.result,
                    "is_error": event.is_error,
                })

            elif isinstance(event, AssistantTurnComplete):
                await send_callback({"type": "assistant_done"})

            elif isinstance(event, PermissionRequestEvent):
                await send_callback({
                    "type": "permission_request",
                    "tool_name": event.tool_name,
                    "arguments": event.arguments,
                    "reason": event.reason,
                })
                return full_response

            elif isinstance(event, PermissionResultEvent):
                await send_callback({
                    "type": "permission_result",
                    "approved": event.approved,
                    "reason": event.reason,
                })

            elif isinstance(event, ErrorEvent):
                await send_callback({
                    "type": "error",
                    "message": f"{type(event.error).__name__}: {event.error}",
                })

        return full_response

    async def collect_memory(
        self,
        user_message: str,
        assistant_response: str,
    ) -> None:
        """Collect memory from a conversation turn.

        This runs asynchronously in the background.
        """
        if self._memory_collector is None or self._provider is None:
            return

        try:
            self._memory_collector.collect_from_turn(
                user_message,
                assistant_response,
                self._provider,
            )
        except Exception:
            pass  # Memory collection failures should not break chat
