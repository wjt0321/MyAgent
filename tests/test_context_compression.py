"""Tests for context compression."""

from __future__ import annotations

import pytest

from myagent.engine.context_compression import (
    AutoCompactor,
    ContextCompressor,
    CompressionResult,
    estimate_tokens,
    estimate_message_tokens,
)
from myagent.engine.messages import ConversationMessage, TextBlock, ToolResultBlock


class TestEstimateTokens:
    def test_empty_text(self):
        assert estimate_tokens("") == 0

    def test_short_text(self):
        assert estimate_tokens("hello") == 1

    def test_long_text(self):
        text = "a" * 300
        assert estimate_tokens(text) == 100


class TestContextCompressor:
    def test_no_compression_needed(self):
        messages = [
            ConversationMessage.from_system_text("You are helpful."),
            ConversationMessage.from_user_text("Hello"),
        ]
        compressor = ContextCompressor(max_tokens=10000)
        result = compressor.compress(messages)
        assert result.strategy_used == "none"
        assert len(result.messages) == 2

    def test_truncate_tool_results(self):
        long_content = "x" * 5000
        messages = [
            ConversationMessage.from_system_text("You are helpful."),
            ConversationMessage(
                role="user",
                content=[ToolResultBlock(tool_use_id="1", content=long_content)],
            ),
        ]
        # Use a small max_tokens to force truncation
        compressor = ContextCompressor(max_tokens=50)
        result = compressor.compress(messages)
        # Should use some compression strategy
        assert result.strategy_used in ("truncate_tools", "sliding_window")

    def test_sliding_window(self):
        messages = [
            ConversationMessage.from_system_text("You are helpful."),
        ]
        for i in range(20):
            messages.append(ConversationMessage.from_user_text(f"Message {i}: " + "x" * 500))

        compressor = ContextCompressor(max_tokens=1000, preserve_recent=2)
        result = compressor.compress(messages)
        assert result.strategy_used in ("truncate_tools", "summarize", "sliding_window")
        # Should have system + some recent messages
        assert len(result.messages) < len(messages)
        assert result.messages[0].role == "system"

    def test_summarize_old_messages(self):
        def mock_summarizer(msgs):
            return f"Summary of {len(msgs)} messages"

        messages = [
            ConversationMessage.from_system_text("You are helpful."),
            ConversationMessage.from_user_text("First message"),
            ConversationMessage.from_user_text("Second message"),
            ConversationMessage.from_user_text("Third message"),
            ConversationMessage.from_user_text("Fourth message"),
        ]
        compressor = ContextCompressor(
            max_tokens=50,
            preserve_recent=2,
            summarizer=mock_summarizer,
        )
        result = compressor.compress(messages)
        # Should use some compression strategy or none if it fits
        assert result.strategy_used in ("none", "summarize", "sliding_window")


class TestAutoCompactor:
    def test_should_compact_when_over_threshold(self):
        compressor = ContextCompressor(max_tokens=100)
        compactor = AutoCompactor(compressor, threshold_ratio=0.5)
        messages = [
            ConversationMessage.from_system_text("You are helpful."),
            ConversationMessage.from_user_text("x" * 300),
        ]
        assert compactor.should_compact(messages) is True

    def test_should_not_compact_when_under_threshold(self):
        compressor = ContextCompressor(max_tokens=10000)
        compactor = AutoCompactor(compressor, threshold_ratio=0.5)
        messages = [
            ConversationMessage.from_system_text("You are helpful."),
            ConversationMessage.from_user_text("Hello"),
        ]
        assert compactor.should_compact(messages) is False

    def test_compact_returns_same_when_not_needed(self):
        compressor = ContextCompressor(max_tokens=10000)
        compactor = AutoCompactor(compressor)
        messages = [
            ConversationMessage.from_system_text("You are helpful."),
            ConversationMessage.from_user_text("Hello"),
        ]
        result = compactor.compact(messages)
        assert result.strategy_used == "none"
        assert len(result.messages) == 2
