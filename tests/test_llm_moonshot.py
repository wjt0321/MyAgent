"""Tests for Moonshot (Kimi) LLM provider."""

from __future__ import annotations

import pytest

from myagent.engine.messages import ConversationMessage
from myagent.llm.providers.moonshot import MoonshotProvider
from myagent.llm.types import DoneChunk, TextChunk, ToolUseChunk


class TestMoonshotProvider:
    def test_provider_creation(self):
        provider = MoonshotProvider(api_key="test-key", model="moonshot-v1-8k")
        assert provider.name == "moonshot"
        assert provider.model == "moonshot-v1-8k"

    def test_provider_default_base_url(self):
        provider = MoonshotProvider(api_key="test", model="moonshot-v1-8k")
        assert provider.base_url == "https://api.moonshot.cn/v1"

    def test_messages_to_moonshot_format(self):
        provider = MoonshotProvider(api_key="test", model="moonshot-v1-8k")
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

    def test_tools_to_moonshot_format(self):
        provider = MoonshotProvider(api_key="test", model="moonshot-v1-8k")
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
        provider = MoonshotProvider(api_key="test", model="moonshot-v1-8k")
        event = {
            "choices": [{"delta": {"content": "Hello"}}],
        }

        chunk = provider._parse_event(event)
        assert isinstance(chunk, TextChunk)
        assert chunk.text == "Hello"

    def test_parse_tool_calls(self):
        provider = MoonshotProvider(api_key="test", model="moonshot-v1-8k")
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
        provider = MoonshotProvider(api_key="test", model="moonshot-v1-8k")
        event = {"choices": [{"delta": {}, "finish_reason": "stop"}]}

        chunk = provider._parse_event(event)
        assert isinstance(chunk, DoneChunk)
