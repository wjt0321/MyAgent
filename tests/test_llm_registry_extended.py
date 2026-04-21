"""Extended tests for LLM provider registry with Chinese providers."""

from __future__ import annotations

import pytest

from myagent.llm.providers.deepseek import DeepSeekProvider
from myagent.llm.providers.minimax import MiniMaxProvider
from myagent.llm.providers.moonshot import MoonshotProvider
from myagent.llm.providers.zhipu import ZhipuProvider
from myagent.llm.registry import ProviderRegistry


class TestProviderRegistryExtended:
    def test_registry_has_chinese_providers(self):
        registry = ProviderRegistry.with_defaults()
        providers = registry.list_providers()
        assert "deepseek" in providers
        assert "zhipu" in providers
        assert "moonshot" in providers
        assert "minimax" in providers

    def test_create_deepseek(self):
        registry = ProviderRegistry.with_defaults()
        provider = registry.create("deepseek", api_key="test", model="deepseek-chat")
        assert isinstance(provider, DeepSeekProvider)

    def test_create_zhipu(self):
        registry = ProviderRegistry.with_defaults()
        provider = registry.create("zhipu", api_key="test", model="glm-4")
        assert isinstance(provider, ZhipuProvider)

    def test_create_moonshot(self):
        registry = ProviderRegistry.with_defaults()
        provider = registry.create("moonshot", api_key="test", model="moonshot-v1-8k")
        assert isinstance(provider, MoonshotProvider)

    def test_create_minimax(self):
        registry = ProviderRegistry.with_defaults()
        provider = registry.create("minimax", api_key="test", model="abab6.5s-chat")
        assert isinstance(provider, MiniMaxProvider)

    def test_create_deepseek_from_config(self):
        registry = ProviderRegistry.with_defaults()
        config = {
            "provider": "deepseek",
            "api_key": "test-key",
            "model": "deepseek-reasoner",
        }
        provider = registry.create_from_config(config)
        assert isinstance(provider, DeepSeekProvider)
        assert provider.model == "deepseek-reasoner"

    def test_create_zhipu_from_config(self):
        registry = ProviderRegistry.with_defaults()
        config = {
            "provider": "zhipu",
            "api_key": "test-key",
            "model": "glm-4-plus",
        }
        provider = registry.create_from_config(config)
        assert isinstance(provider, ZhipuProvider)
        assert provider.model == "glm-4-plus"
