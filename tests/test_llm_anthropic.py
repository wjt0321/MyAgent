"""Tests for Anthropic LLM provider."""

from __future__ import annotations

import pytest

from myagent.engine.messages import ConversationMessage
from myagent.llm.providers.anthropic import AnthropicProvider
from myagent.llm.types import DoneChunk, TextChunk, ToolUseChunk


class TestAnthropicProvider:
    def test_provider_creation(self):
        provider = AnthropicProvider(api_key="test-key", model="claude-3-sonnet-20240229")
        assert provider.name == "anthropic"
        assert provider.model == "claude-3-sonnet-20240229"
        assert provider.api_key == "test-key"

    def test_provider_default_base_url(self):
        provider = AnthropicProvider(api_key="test", model="claude-3")
        assert provider.base_url == "https://api.anthropic.com"

    def test_messages_to_anthropic_format(self):
        provider = AnthropicProvider(api_key="test", model="claude-3")
        messages = [
            ConversationMessage.from_system_text("You are helpful."),
            ConversationMessage.from_user_text("Hello"),
        ]

        result = provider._convert_messages(messages)
        assert result["system"] == "You are helpful."
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"] == [{"type": "text", "text": "Hello"}]

    def test_tools_to_anthropic_format(self):
        provider = AnthropicProvider(api_key="test", model="claude-3")
        tools = [
            {
                "name": "Read",
                "description": "Read a file",
                "input_schema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            }
        ]

        result = provider._convert_tools(tools)
        assert len(result) == 1
        assert result[0]["name"] == "Read"
        assert result[0]["input_schema"]["type"] == "object"

    def test_parse_text_delta(self):
        provider = AnthropicProvider(api_key="test", model="claude-3")
        event = {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": "Hello"},
        }

        chunk = provider._parse_event(event)
        assert isinstance(chunk, TextChunk)
        assert chunk.text == "Hello"

    def test_parse_tool_use(self):
        provider = AnthropicProvider(api_key="test", model="claude-3")
        event = {
            "type": "content_block_start",
            "content_block": {
                "type": "tool_use",
                "id": "tool_1",
                "name": "Read",
                "input": {"path": "/tmp/test.txt"},
            },
        }

        chunk = provider._parse_event(event)
        assert isinstance(chunk, ToolUseChunk)
        assert chunk.id == "tool_1"
        assert chunk.name == "Read"
        assert chunk.input == {"path": "/tmp/test.txt"}

    def test_parse_done(self):
        provider = AnthropicProvider(api_key="test", model="claude-3")
        event = {"type": "message_stop"}

        chunk = provider._parse_event(event)
        assert isinstance(chunk, DoneChunk)

    def test_parse_unknown_event(self):
        provider = AnthropicProvider(api_key="test", model="claude-3")
        event = {"type": "ping"}

        chunk = provider._parse_event(event)
        assert chunk is None
