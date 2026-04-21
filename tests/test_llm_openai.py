"""Tests for OpenAI LLM provider."""

from __future__ import annotations

import pytest

from myagent.engine.messages import ConversationMessage
from myagent.llm.providers.openai import OpenAIProvider
from myagent.llm.types import DoneChunk, TextChunk, ToolUseChunk


class TestOpenAIProvider:
    def test_provider_creation(self):
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o")
        assert provider.name == "openai"
        assert provider.model == "gpt-4o"
        assert provider.api_key == "test-key"

    def test_provider_default_base_url(self):
        provider = OpenAIProvider(api_key="test", model="gpt-4")
        assert provider.base_url == "https://api.openai.com/v1"

    def test_provider_custom_base_url(self):
        provider = OpenAIProvider(
            api_key="test", model="gpt-4", base_url="https://custom.openai.com/v1"
        )
        assert provider.base_url == "https://custom.openai.com/v1"

    def test_messages_to_openai_format(self):
        provider = OpenAIProvider(api_key="test", model="gpt-4")
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

    def test_tools_to_openai_format(self):
        provider = OpenAIProvider(api_key="test", model="gpt-4")
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
        assert result[0]["function"]["parameters"]["type"] == "object"

    def test_parse_text_delta(self):
        provider = OpenAIProvider(api_key="test", model="gpt-4")
        event = {
            "choices": [{"delta": {"content": "Hello"}}],
        }

        chunk = provider._parse_event(event)
        assert isinstance(chunk, TextChunk)
        assert chunk.text == "Hello"

    def test_parse_tool_calls(self):
        provider = OpenAIProvider(api_key="test", model="gpt-4")
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
        assert chunk.input == {"path": "/tmp/test.txt"}

    def test_parse_done(self):
        provider = OpenAIProvider(api_key="test", model="gpt-4")
        event = {"choices": [{"delta": {}, "finish_reason": "stop"}]}

        chunk = provider._parse_event(event)
        assert isinstance(chunk, DoneChunk)

    def test_parse_empty_delta(self):
        provider = OpenAIProvider(api_key="test", model="gpt-4")
        event = {"choices": [{"delta": {}}]}

        chunk = provider._parse_event(event)
        assert chunk is None
