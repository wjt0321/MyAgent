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
from myagent.llm.base import BaseProvider
from myagent.llm.providers.alibaba import AlibabaProvider
from myagent.llm.providers.alibaba_cn import AlibabaCNProvider
from myagent.llm.providers.anthropic import AnthropicProvider
from myagent.llm.providers.arcee import ArceeProvider
from myagent.llm.providers.deepseek import DeepSeekProvider
from myagent.llm.providers.gemini import GeminiProvider
from myagent.llm.providers.huggingface import HuggingFaceProvider
from myagent.llm.providers.minimax import MiniMaxProvider
from myagent.llm.providers.minimax_cn import MiniMaxCNProvider
from myagent.llm.providers.moonshot import MoonshotProvider
from myagent.llm.providers.moonshot_cn import MoonshotCNProvider
from myagent.llm.providers.nvidia import NvidiaProvider
from myagent.llm.providers.ollama import OllamaProvider
from myagent.llm.providers.openai import OpenAIProvider
from myagent.llm.providers.openrouter import OpenRouterProvider
from myagent.llm.providers.xai import XAIProvider
from myagent.llm.providers.xiaomi import XiaomiProvider
from myagent.llm.providers.zhipu import ZhipuProvider
from myagent.llm.providers.zhipu_cn import ZhipuCNProvider
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


# ---------------------------------------------------------------------------
# Provider auto-discovery
# ---------------------------------------------------------------------------

_PROVIDER_ENV_MAP: list[tuple[str, type[BaseProvider], str, str, str]] = [
    # (env_var, provider_class, default_model, default_base_url, provider_name)
    ("ANTHROPIC_API_KEY", AnthropicProvider, "claude-sonnet-4-20250514", "", "anthropic"),
    ("OPENAI_API_KEY", OpenAIProvider, "gpt-4o", "", "openai"),
    ("DEEPSEEK_API_KEY", DeepSeekProvider, "deepseek-chat", "", "deepseek"),
    ("ZHIPU_API_KEY", ZhipuProvider, "glm-4", "", "zhipu"),
    ("ZHIPU_CN_API_KEY", ZhipuCNProvider, "glm-4", "", "zhipu-cn"),
    ("MOONSHOT_API_KEY", MoonshotProvider, "moonshot-v1-8k", "", "moonshot"),
    ("MOONSHOT_CN_API_KEY", MoonshotCNProvider, "moonshot-v1-8k", "", "moonshot-cn"),
    ("MINIMAX_API_KEY", MiniMaxProvider, "abab6.5s-chat", "", "minimax"),
    ("MINIMAX_CN_API_KEY", MiniMaxCNProvider, "abab6.5s-chat", "", "minimax-cn"),
    ("OPENROUTER_API_KEY", OpenRouterProvider, "openai/gpt-4o", "", "openrouter"),
    ("XAI_API_KEY", XAIProvider, "grok-3", "", "xai"),
    ("GEMINI_API_KEY", GeminiProvider, "gemini-2.5-pro", "", "gemini"),
    ("DASHSCOPE_API_KEY", AlibabaProvider, "qwen-max", "", "alibaba"),
    ("DASHSCOPE_CN_API_KEY", AlibabaCNProvider, "qwen-max", "", "alibaba-cn"),
    ("HF_API_KEY", HuggingFaceProvider, "meta-llama/Llama-3.3-70B-Instruct", "", "huggingface"),
    ("NVIDIA_API_KEY", NvidiaProvider, "nvidia/llama-3.3-nemotron-super-49b-v1", "", "nvidia"),
    ("ARCEE_API_KEY", ArceeProvider, "trinity-large-thinking", "", "arcee"),
    ("XIAOMI_API_KEY", XiaomiProvider, "mimo-v2-pro", "", "xiaomi"),
]


def _get_env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def _detect_provider_from_model(model: str) -> tuple[type[BaseProvider] | None, str]:
    """Auto-detect provider class and resolved model from a model string.

    Supports:
      - provider/model syntax: "anthropic/claude-sonnet-4" → (AnthropicProvider, "claude-sonnet-4")
      - bare model names with heuristic matching
    """
    if not model:
        return None, ""

    model_lower = model.lower().strip()

    # provider/model syntax
    if "/" in model_lower and not model_lower.startswith("http"):
        parts = model.split("/", 1)
        provider_part = parts[0].lower().strip()
        model_part = parts[1].strip()

        provider_map: dict[str, type[BaseProvider]] = {
            "anthropic": AnthropicProvider,
            "claude": AnthropicProvider,
            "openai": OpenAIProvider,
            "gpt": OpenAIProvider,
            "deepseek": DeepSeekProvider,
            "zhipu": ZhipuProvider,
            "zhipu-cn": ZhipuCNProvider,
            "glm": ZhipuProvider,
            "moonshot": MoonshotProvider,
            "moonshot-cn": MoonshotCNProvider,
            "kimi": MoonshotProvider,
            "kimi-cn": MoonshotCNProvider,
            "minimax": MiniMaxProvider,
            "minimax-cn": MiniMaxCNProvider,
            "openrouter": OpenRouterProvider,
            "or": OpenRouterProvider,
            "xai": XAIProvider,
            "grok": XAIProvider,
            "gemini": GeminiProvider,
            "google": GeminiProvider,
            "alibaba": AlibabaProvider,
            "alibaba-cn": AlibabaCNProvider,
            "qwen": AlibabaProvider,
            "qwen-cn": AlibabaCNProvider,
            "dashscope": AlibabaProvider,
            "dashscope-cn": AlibabaCNProvider,
            "huggingface": HuggingFaceProvider,
            "hf": HuggingFaceProvider,
            "nvidia": NvidiaProvider,
            "arcee": ArceeProvider,
            "xiaomi": XiaomiProvider,
            "mimo": XiaomiProvider,
            "ollama": OllamaProvider,
        }

        if provider_part in provider_map:
            return provider_map[provider_part], model_part

    # Heuristic: bare model name → provider
    heuristic_map: list[tuple[str, type[BaseProvider]]] = [
        ("claude-", AnthropicProvider),
        ("gpt-", OpenAIProvider),
        ("o1", OpenAIProvider),
        ("o3", OpenAIProvider),
        ("o4", OpenAIProvider),
        ("deepseek-", DeepSeekProvider),
        ("glm-", ZhipuProvider),
        ("moonshot-", MoonshotProvider),
        ("abab", MiniMaxProvider),
        ("grok-", XAIProvider),
        ("gemini-", GeminiProvider),
        ("qwen-", AlibabaProvider),
        ("qwq-", AlibabaProvider),
        ("trinity-", ArceeProvider),
        ("mimo-", XiaomiProvider),
        ("llama", OllamaProvider),
        ("qwen2", OllamaProvider),
    ]

    for prefix, provider_cls in heuristic_map:
        if model_lower.startswith(prefix):
            return provider_cls, model

    return None, model


def _create_provider(model: str | None = None) -> BaseProvider | None:
    """Create the best available LLM provider from environment variables.

    If *model* is provided, tries to create a provider matching that model.
    Otherwise picks the first provider with credentials in the env.
    """
    # If a model is specified, try to match it to a provider
    if model:
        provider_cls, resolved_model = _detect_provider_from_model(model)
        if provider_cls:
            # Find the env var for this provider
            for env_var, cls, default_model, default_base, name in _PROVIDER_ENV_MAP:
                if cls is provider_cls:
                    api_key = _get_env(env_var, "")
                    if api_key:
                        base_url = _get_env(f"{name.upper()}_BASE_URL", default_base or None)
                        kwargs: dict[str, Any] = {}
                        if base_url:
                            kwargs["base_url"] = base_url
                        return provider_cls(api_key=api_key, model=resolved_model or default_model, **kwargs)
            # Fallback: try common API keys
            api_key = (
                _get_env("OPENAI_API_KEY", "")
                or _get_env("OPENROUTER_API_KEY", "")
                or _get_env("ANTHROPIC_API_KEY", "")
            )
            if api_key and provider_cls is not OllamaProvider:
                return provider_cls(api_key=api_key, model=resolved_model)
            if provider_cls is OllamaProvider:
                return OllamaProvider(model=resolved_model)

    # No model specified — pick first available provider from env
    for env_var, provider_cls, default_model, default_base, name in _PROVIDER_ENV_MAP:
        api_key = _get_env(env_var, "")
        if api_key:
            base_url = _get_env(f"{name.upper()}_BASE_URL", default_base or None)
            kwargs: dict[str, Any] = {}
            if base_url:
                kwargs["base_url"] = base_url
            return provider_cls(api_key=api_key, model=default_model, **kwargs)

    # Ollama doesn't need an API key
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:11434/v1/models", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                return OllamaProvider()
    except Exception:
        pass

    return None


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
        self._provider: BaseProvider | None = None
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

    def _init_provider(self, model: str | None = None) -> None:
        self._provider = _create_provider(model)

    def is_configured(self) -> bool:
        return self._provider is not None

    def create_engine(self, agent_name: str = "general", model: str | None = None) -> QueryEngine | None:
        """Create a QueryEngine for the given agent and optional model override."""
        # If model is specified and different from current provider's model, re-init
        if model and self._provider is not None:
            if hasattr(self._provider, "model") and self._provider.model != model:
                self._init_provider(model)
        elif model and self._provider is None:
            self._init_provider(model)

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
                    "tool_use_id": event.tool_use_id,
                    "arguments": event.arguments,
                })

            elif isinstance(event, ToolExecutionCompleted):
                await send_callback({
                    "type": "tool_result",
                    "tool_use_id": event.tool_use_id,
                    "result": event.result,
                    "is_error": event.is_error,
                })

            elif isinstance(event, AssistantTurnComplete):
                await send_callback({"type": "assistant_done"})

            elif isinstance(event, PermissionRequestEvent):
                await send_callback({
                    "type": "permission_request",
                    "tool_name": event.tool_name,
                    "tool_use_id": event.tool_use_id,
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
