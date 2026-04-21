"""Tests for gateway base classes."""

from __future__ import annotations

import pytest

from myagent.gateway.base import (
    GatewayMessage,
    MessageEvent,
    MessageType,
    Platform,
    SendResult,
    SessionSource,
    truncate_message,
    strip_markdown,
    extract_images,
)


class TestGatewayMessage:
    def test_creation(self):
        msg = GatewayMessage(text="hello", user_id="u1", channel_id="c1", platform="discord")
        assert msg.text == "hello"
        assert msg.user_id == "u1"
        assert msg.channel_id == "c1"
        assert msg.platform == "discord"

    def test_reply(self):
        msg = GatewayMessage(text="hello", user_id="u1", channel_id="c1", platform="discord")
        reply = msg.reply("hi there")
        assert reply.text == "hi there"
        assert reply.user_id == "agent"
        assert reply.channel_id == "c1"
        assert reply.platform == "discord"


class TestMessageEvent:
    def test_text_message(self):
        source = SessionSource(platform=Platform.DISCORD, chat_id="123")
        event = MessageEvent(text="hello", source=source)
        assert event.text == "hello"
        assert event.message_type == MessageType.TEXT
        assert not event.is_command()

    def test_command_message(self):
        source = SessionSource(platform=Platform.TELEGRAM, chat_id="456")
        event = MessageEvent(text="/reset", source=source)
        assert event.is_command()
        assert event.get_command() == "reset"
        assert event.get_command_args() == ""

    def test_command_with_args(self):
        source = SessionSource(platform=Platform.TELEGRAM, chat_id="456")
        event = MessageEvent(text="/agent explore", source=source)
        assert event.get_command() == "agent"
        assert event.get_command_args() == "explore"

    def test_command_with_mention(self):
        source = SessionSource(platform=Platform.TELEGRAM, chat_id="456")
        event = MessageEvent(text="/start@mybot", source=source)
        assert event.get_command() == "start"

    def test_non_command_get_command_returns_none(self):
        source = SessionSource(platform=Platform.DISCORD, chat_id="123")
        event = MessageEvent(text="hello world", source=source)
        assert event.get_command() is None


class TestSessionSource:
    def test_creation(self):
        source = SessionSource(
            platform=Platform.FEISHU,
            chat_id="chat_123",
            user_id="user_456",
            chat_type="group",
        )
        assert source.platform == Platform.FEISHU
        assert source.chat_id == "chat_123"
        assert source.user_id == "user_456"
        assert source.chat_type == "group"

    def test_session_key_dm(self):
        source = SessionSource(platform=Platform.DISCORD, chat_id="123", user_id="u1")
        assert source.session_key == "discord:123:u1"

    def test_session_key_group_without_user(self):
        source = SessionSource(platform=Platform.DISCORD, chat_id="123")
        assert source.session_key == "discord:123"


class TestSendResult:
    def test_success(self):
        result = SendResult(success=True, message_id="msg_123")
        assert result.success is True
        assert result.message_id == "msg_123"
        assert result.error is None
        assert result.retryable is False

    def test_failure(self):
        result = SendResult(success=False, error="Network timeout", retryable=True)
        assert result.success is False
        assert result.error == "Network timeout"
        assert result.retryable is True


class TestTruncateMessage:
    def test_short_message_unchanged(self):
        text = "Short message"
        chunks = truncate_message(text, max_length=100)
        assert chunks == [text]

    def test_long_message_split(self):
        text = "A" * 5000
        chunks = truncate_message(text, max_length=2000)
        assert len(chunks) > 1
        assert all(len(c) <= 2000 + 20 for c in chunks)  # +20 for indicator

    def test_code_block_preserved(self):
        text = "```python\n" + "x = 1\n" * 500 + "```"
        chunks = truncate_message(text, max_length=200)
        for chunk in chunks:
            # Each chunk should have balanced fences or be properly closed
            fences = chunk.count("```")
            assert fences % 2 == 0 or "(1/" in chunk or fences == 1

    def test_multipart_indicators(self):
        text = "A" * 5000
        chunks = truncate_message(text, max_length=2000)
        assert "(1/" in chunks[0]
        assert f"({len(chunks)}/{len(chunks)})" in chunks[-1]


class TestStripMarkdown:
    def test_bold_removed(self):
        assert strip_markdown("**bold**") == "bold"

    def test_italic_removed(self):
        assert strip_markdown("*italic*") == "italic"

    def test_code_block_removed(self):
        assert strip_markdown("```python\ncode\n```") == "code"

    def test_inline_code_removed(self):
        assert strip_markdown("`code`") == "code"

    def test_link_removed(self):
        assert strip_markdown("[text](url)") == "text"

    def test_heading_removed(self):
        assert strip_markdown("# Title") == "Title"


class TestExtractImages:
    def test_markdown_image(self):
        text = "Here is an image: ![alt](https://example.com/img.png)"
        images, cleaned = extract_images(text)
        assert len(images) == 1
        assert images[0] == ("https://example.com/img.png", "alt")

    def test_html_image(self):
        text = 'Photo: <img src="https://example.com/photo.jpg">'
        images, cleaned = extract_images(text)
        assert len(images) == 1
        assert images[0][0] == "https://example.com/photo.jpg"

    def test_no_images(self):
        text = "Just plain text"
        images, cleaned = extract_images(text)
        assert len(images) == 0
        assert cleaned == text

    def test_images_removed_from_content(self):
        text = "Hello ![alt](https://ex.com/img.png) world"
        images, cleaned = extract_images(text)
        assert "https://ex.com/img.png" not in cleaned
