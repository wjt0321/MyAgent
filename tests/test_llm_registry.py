"""Tests for LLM provider registry."""

from __future__ import annotations

import pytest

from myagent.llm.base import BaseProvider
from myagent.llm.providers.anthropic import AnthropicProvider
from myagent.llm.providers.openai import OpenAIProvider
from myagent.llm.providers.openrouter import OpenRouterProvider
from myagent.llm.registry import ProviderRegistry


class TestProviderRegistry:
    def test_registry_creation(self):
        registry = ProviderRegistry()
        assert registry.list_providers() == []

    def test_register_provider(self):
        registry = ProviderRegistry()
        registry.register("anthropic", AnthropicProvider)
        assert "anthropic" in registry.list_providers()

    def test_get_provider_class(self):
        registry = ProviderRegistry()
        registry.register("anthropic", AnthropicProvider)
        assert registry.get("anthropic") is AnthropicProvider

    def test_get_nonexistent_provider(self):
        registry = ProviderRegistry()
        assert registry.get("nonexistent") is None

    def test_default_registry_has_builtin_providers(self):
        registry = ProviderRegistry.with_defaults()
        providers = registry.list_providers()
        assert "anthropic" in providers
        assert "openai" in providers
        assert "openrouter" in providers

    def test_create_provider_instance(self):
        registry = ProviderRegistry.with_defaults()
        provider = registry.create(
            "anthropic",
            api_key="test-key",
            model="claude-3-sonnet-20240229",
        )
        assert isinstance(provider, AnthropicProvider)
        assert provider.api_key == "test-key"
        assert provider.model == "claude-3-sonnet-20240229"

    def test_create_openai_instance(self):
        registry = ProviderRegistry.with_defaults()
        provider = registry.create(
            "openai",
            api_key="test-key",
            model="gpt-4o",
        )
        assert isinstance(provider, OpenAIProvider)
        assert provider.model == "gpt-4o"

    def test_create_unknown_provider_raises(self):
        registry = ProviderRegistry()
        with pytest.raises(ValueError, match="Unknown provider"):
            registry.create("unknown", api_key="test")

    def test_create_from_config(self):
        registry = ProviderRegistry.with_defaults()
        config = {
            "provider": "anthropic",
            "api_key": "test-key",
            "model": "claude-3-opus-20240229",
        }
        provider = registry.create_from_config(config)
        assert isinstance(provider, AnthropicProvider)
        assert provider.model == "claude-3-opus-20240229"

    def test_create_from_config_with_base_url(self):
        registry = ProviderRegistry.with_defaults()
        config = {
            "provider": "openai",
            "api_key": "test-key",
            "model": "gpt-4",
            "base_url": "https://custom.openai.com/v1",
        }
        provider = registry.create_from_config(config)
        assert isinstance(provider, OpenAIProvider)
        assert provider.base_url == "https://custom.openai.com/v1"
