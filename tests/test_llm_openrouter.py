"""Tests for OpenRouter LLM provider."""

from __future__ import annotations

from myagent.llm.providers.openrouter import OpenRouterProvider


class TestOpenRouterProvider:
    def test_provider_creation(self):
        provider = OpenRouterProvider(api_key="test-key", model="anthropic/claude-3.5-sonnet")
        assert provider.name == "openrouter"
        assert provider.model == "anthropic/claude-3.5-sonnet"

    def test_provider_default_base_url(self):
        provider = OpenRouterProvider(api_key="test", model="gpt-4o")
        assert provider.base_url == "https://openrouter.ai/api/v1"

    def test_provider_inherits_openai(self):
        provider = OpenRouterProvider(api_key="test", model="gpt-4o")
        assert hasattr(provider, "stream_messages")
        assert hasattr(provider, "complete")
        assert hasattr(provider, "_convert_messages")
        assert hasattr(provider, "_convert_tools")
