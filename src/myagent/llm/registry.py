"""Provider registry for MyAgent LLM integrations."""

from __future__ import annotations

from typing import Any, Type

from myagent.llm.base import BaseProvider
from myagent.llm.providers.alibaba import AlibabaProvider
from myagent.llm.providers.anthropic import AnthropicProvider
from myagent.llm.providers.arcee import ArceeProvider
from myagent.llm.providers.deepseek import DeepSeekProvider
from myagent.llm.providers.gemini import GeminiProvider
from myagent.llm.providers.huggingface import HuggingFaceProvider
from myagent.llm.providers.minimax import MiniMaxProvider
from myagent.llm.providers.moonshot import MoonshotProvider
from myagent.llm.providers.nvidia import NvidiaProvider
from myagent.llm.providers.ollama import OllamaProvider
from myagent.llm.providers.openai import OpenAIProvider
from myagent.llm.providers.openrouter import OpenRouterProvider
from myagent.llm.providers.xai import XAIProvider
from myagent.llm.providers.xiaomi import XiaomiProvider
from myagent.llm.providers.zhipu import ZhipuProvider


class ProviderRegistry:
    """Registry for LLM provider classes."""

    def __init__(self) -> None:
        self._providers: dict[str, Type[BaseProvider]] = {}

    def register(self, name: str, provider_class: Type[BaseProvider]) -> None:
        """Register a provider class."""
        self._providers[name] = provider_class

    def get(self, name: str) -> Type[BaseProvider] | None:
        """Get a provider class by name."""
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._providers.keys())

    def create(self, name: str, **kwargs: Any) -> BaseProvider:
        """Create a provider instance by name."""
        provider_class = self.get(name)
        if provider_class is None:
            raise ValueError(f"Unknown provider: {name}")
        return provider_class(**kwargs)

    def create_from_config(self, config: dict[str, Any]) -> BaseProvider:
        """Create a provider from a configuration dict."""
        name = config.pop("provider")
        return self.create(name, **config)

    @classmethod
    def with_defaults(cls) -> ProviderRegistry:
        """Create a registry with built-in providers pre-registered."""
        registry = cls()
        registry.register("alibaba", AlibabaProvider)
        registry.register("anthropic", AnthropicProvider)
        registry.register("arcee", ArceeProvider)
        registry.register("deepseek", DeepSeekProvider)
        registry.register("gemini", GeminiProvider)
        registry.register("huggingface", HuggingFaceProvider)
        registry.register("minimax", MiniMaxProvider)
        registry.register("moonshot", MoonshotProvider)
        registry.register("nvidia", NvidiaProvider)
        registry.register("ollama", OllamaProvider)
        registry.register("openai", OpenAIProvider)
        registry.register("openrouter", OpenRouterProvider)
        registry.register("xai", XAIProvider)
        registry.register("xiaomi", XiaomiProvider)
        registry.register("zhipu", ZhipuProvider)
        return registry
