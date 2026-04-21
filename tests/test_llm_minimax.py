"""Tests for MiniMax LLM provider."""

from __future__ import annotations

import pytest

from myagent.engine.messages import ConversationMessage
from myagent.llm.providers.minimax import MiniMaxProvider
from myagent.llm.types import DoneChunk, TextChunk, ToolUseChunk


class TestMiniMaxProvider:
    def test_provider_creation(self):
        provider = MiniMaxProvider(api_key="test-key", model="abab6.5s-chat")
        assert provider.name == "minimax"
        assert provider.model == "abab6.5s-chat"

    def test_provider_default_base_url(self):
        provider = MiniMaxProvider(api_key="test", model="abab6.5s-chat")
        assert provider.base_url == "https://api.minimax.chat/v1"

    def test_messages_to_minimax_format(self):
        provider = MiniMaxProvider(api_key="test", model="abab6.5s-chat")
        messages = [
            ConversationMessage.from_system_text("You are helpful."),
            ConversationMessage.from_user_text("Hello"),
        ]

        result = provider._convert_messages(messages)
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are helpful."
        assert result[1]["role"] == "user"
        assert result[1]["content"] == "Hello"

    def test_tools_to_minimax_format(self):
        provider = MiniMaxProvider(api_key="test", model="abab6.5s-chat")
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
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "Read"

    def test_parse_text_delta(self):
        provider = MiniMaxProvider(api_key="test", model="abab6.5s-chat")
        event = {
            "choices": [{"delta": {"content": "Hello"}}],
        }

        chunk = provider._parse_event(event)
        assert isinstance(chunk, TextChunk)
        assert chunk.text == "Hello"

    def test_parse_tool_calls(self):
        provider = MiniMaxProvider(api_key="test", model="abab6.5s-chat")
        event = {
            "choices": [{
                "delta": {
                    "tool_calls": [{
                        "index": 0,
                        "id": "call_1",
                        "function": {
                            "name": "Read",
                            "arguments": '{"path": "/tmp/test.txt"}',
                        },
                    }]
                }
            }],
        }

        chunk = provider._parse_event(event)
        assert isinstance(chunk, ToolUseChunk)
        assert chunk.id == "call_1"
        assert chunk.name == "Read"

    def test_parse_done(self):
        provider = MiniMaxProvider(api_key="test", model="abab6.5s-chat")
        event = {"choices": [{"delta": {}, "finish_reason": "stop"}]}

        chunk = provider._parse_event(event)
        assert isinstance(chunk, DoneChunk)
