"""Tests for myagent LLM providers."""

from __future__ import annotations

import pytest

from myagent.llm.base import BaseProvider
from myagent.llm.types import (
    DoneChunk,
    StreamChunk,
    TextChunk,
    ToolUseChunk,
)


class TestStreamChunkTypes:
    def test_text_chunk_creation(self):
        chunk = TextChunk(text="Hello")
        assert chunk.text == "Hello"
        assert isinstance(chunk, StreamChunk)

    def test_tool_use_chunk_creation(self):
        chunk = ToolUseChunk(id="t1", name="Read", input={"path": "/tmp/test.txt"})
        assert chunk.id == "t1"
        assert chunk.name == "Read"
        assert chunk.input == {"path": "/tmp/test.txt"}
        assert isinstance(chunk, StreamChunk)

    def test_done_chunk_creation(self):
        chunk = DoneChunk()
        assert isinstance(chunk, StreamChunk)


class TestBaseProvider:
    def test_base_provider_is_abstract(self):
        with pytest.raises(TypeError):
            BaseProvider()

    def test_base_provider_required_methods(self):
        assert hasattr(BaseProvider, "stream_messages")
        assert hasattr(BaseProvider, "complete")

    def test_base_provider_name_attribute(self):
        class FakeProvider(BaseProvider):
            name = "fake"

            async def stream_messages(self, messages, tools=None):
                yield TextChunk(text="hi")

            async def complete(self, messages, tools=None):
                return "hi"

        provider = FakeProvider(api_key="test", model="fake-model")
        assert provider.name == "fake"
        assert provider.model == "fake-model"
