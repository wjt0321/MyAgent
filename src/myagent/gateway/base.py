"""Gateway base classes for MyAgent.

Inspired by Hermes Agent's gateway design — unified message model,
platform adapters, and session management.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Platform(Enum):
    """Supported messaging platforms."""

    LOCAL = "local"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    FEISHU = "feishu"  # Lark
    WEIXIN = "weixin"  # WeChat
    WECOM = "wecom"    # Enterprise WeChat
    QQ = "qq"
    DINGTALK = "dingtalk"
    MATRIX = "matrix"
    WEBHOOK = "webhook"


class MessageType(Enum):
    """Types of incoming messages."""

    TEXT = "text"
    COMMAND = "command"
    PHOTO = "photo"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    VOICE = "voice"
    DOCUMENT = "document"
    FILE = "file"
    LOCATION = "location"
    STICKER = "sticker"


class ProcessingOutcome(Enum):
    """Result classification for message processing lifecycle."""

    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SessionSource:
    """Source information for a message."""

    platform: Platform
    chat_id: str
    chat_name: Optional[str] = None
    chat_type: str = "dm"  # "dm", "group", "channel"
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    thread_id: Optional[str] = None
    chat_topic: Optional[str] = None
    is_bot: bool = False

    @property
    def session_key(self) -> str:
        """Build a session key for this source."""
        parts = [self.platform.value, self.chat_id]
        if self.user_id:
            parts.append(self.user_id)
        return ":".join(parts)


@dataclass
class MessageEvent:
    """Incoming message from a platform — normalized representation."""

    text: str
    message_type: MessageType = MessageType.TEXT
    source: Optional[SessionSource] = None
    raw_message: Any = None
    message_id: Optional[str] = None
    platform_update_id: Optional[int] = None
    media_urls: List[str] = field(default_factory=list)
    media_types: List[str] = field(default_factory=list)
    reply_to_message_id: Optional[str] = None
    reply_to_text: Optional[str] = None
    auto_skill: Optional[str | list[str]] = None
    channel_prompt: Optional[str] = None
    internal: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

    def is_command(self) -> bool:
        """Check if this is a command message (e.g., /new, /reset)."""
        return self.text.startswith("/")

    def get_command(self) -> Optional[str]:
        """Extract command name if this is a command message."""
        if not self.is_command():
            return None
        parts = self.text.split(maxsplit=1)
        raw = parts[0][1:].lower() if parts else None
        if raw and "@" in raw:
            raw = raw.split("@", 1)[0]
        if raw and "/" in raw:
            return None
        return raw

    def get_command_args(self) -> str:
        """Get the arguments after a command."""
        if not self.is_command():
            return self.text
        parts = self.text.split(maxsplit=1)
        return parts[1] if len(parts) > 1 else ""


@dataclass
class SendResult:
    """Result of sending a message."""

    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    raw_response: Any = None
    retryable: bool = False


@dataclass
class GatewayMessage:
    """Simplified message for gateway communication."""

    text: str
    user_id: str
    channel_id: str
    platform: str
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def reply(self, text: str) -> GatewayMessage:
        """Create a reply message."""
        return GatewayMessage(
            text=text,
            user_id="agent",
            channel_id=self.channel_id,
            platform=self.platform,
        )


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

MessageHandler = Callable[[MessageEvent], Awaitable[Optional[str]]]


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def strip_markdown(text: str) -> str:
    """Strip markdown formatting for plain-text platforms."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"\*(.+?)\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"_(.+?)_", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"```[a-zA-Z0-9_+-]*\n?", "", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_images(content: str) -> Tuple[List[Tuple[str, str]], str]:
    """Extract image URLs from markdown and HTML image tags.

    Returns:
        Tuple of (list of (url, alt_text) pairs, cleaned content).
    """
    images = []
    cleaned = content

    # Markdown images: ![alt](url)
    md_pattern = r"!\[([^\]]*)\]\((https?://[^\s\)]+)\)"
    for match in re.finditer(md_pattern, content):
        alt_text = match.group(1)
        url = match.group(2)
        images.append((url, alt_text))

    # HTML img tags
    html_pattern = r'<img\s+src=["\']?(https?://[^\s"\'<>]+)["\']?\s*/?>\s*(?:</img>)?'
    for match in re.finditer(html_pattern, content):
        url = match.group(1)
        images.append((url, ""))

    if images:
        extracted_urls = {url for url, _ in images}

        def _remove_if_extracted(match: re.Match) -> str:
            url = match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(1)
            return "" if url in extracted_urls else match.group(0)

        cleaned = re.sub(md_pattern, _remove_if_extracted, cleaned)
        cleaned = re.sub(html_pattern, _remove_if_extracted, cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    return images, cleaned


def truncate_message(
    content: str,
    max_length: int = 4096,
    len_fn: Optional[Callable[[str], int]] = None,
) -> List[str]:
    """Split a long message into chunks, preserving code block boundaries.

    Multi-chunk responses receive indicators like ``(1/3)``.
    """
    _len = len_fn or len
    if _len(content) <= max_length:
        return [content]

    INDICATOR_RESERVE = 10
    FENCE_CLOSE = "\n```"

    chunks: List[str] = []
    remaining = content
    carry_lang: Optional[str] = None

    while remaining:
        prefix = f"```{carry_lang}\n" if carry_lang is not None else ""
        headroom = max_length - INDICATOR_RESERVE - len(prefix) - len(FENCE_CLOSE)
        if headroom < 1:
            headroom = max_length // 2

        if len(prefix) + len(remaining) <= max_length - INDICATOR_RESERVE:
            chunks.append(prefix + remaining)
            break

        region = remaining[:headroom]
        split_at = region.rfind("\n")
        if split_at < headroom // 2:
            split_at = region.rfind(" ")
        if split_at < 1:
            split_at = headroom

        # Avoid splitting inside inline code spans
        candidate = remaining[:split_at]
        backtick_count = candidate.count("`") - candidate.count("\\`")
        if backtick_count % 2 == 1:
            last_bt = candidate.rfind("`")
            while last_bt > 0 and candidate[last_bt - 1] == "\\":
                last_bt = candidate.rfind("`", 0, last_bt)
            if last_bt > 0:
                safe_split = candidate.rfind(" ", 0, last_bt)
                nl_split = candidate.rfind("\n", 0, last_bt)
                safe_split = max(safe_split, nl_split)
                if safe_split > headroom // 4:
                    split_at = safe_split

        chunk_body = remaining[:split_at]
        remaining = remaining[split_at:].lstrip()

        full_chunk = prefix + chunk_body

        # Track code block state
        in_code = carry_lang is not None
        lang = carry_lang or ""
        for line in chunk_body.split("\n"):
            stripped = line.strip()
            if stripped.startswith("```"):
                if in_code:
                    in_code = False
                    lang = ""
                else:
                    in_code = True
                    tag = stripped[3:].strip()
                    lang = tag.split()[0] if tag else ""

        if in_code:
            full_chunk += FENCE_CLOSE
            carry_lang = lang
        else:
            carry_lang = None

        chunks.append(full_chunk)

    if len(chunks) > 1:
        total = len(chunks)
        chunks = [f"{chunk} ({i + 1}/{total})" for i, chunk in enumerate(chunks)]

    return chunks


# ---------------------------------------------------------------------------
# Retryable error detection
# ---------------------------------------------------------------------------

_RETRYABLE_ERROR_PATTERNS = (
    "connecterror",
    "connectionerror",
    "connectionreset",
    "connectionrefused",
    "connecttimeout",
    "network",
    "broken pipe",
    "remotedisconnected",
    "eoferror",
)


def is_retryable_error(error: Optional[str]) -> bool:
    """Return True if the error string looks like a transient network failure."""
    if not error:
        return False
    lowered = error.lower()
    return any(pat in lowered for pat in _RETRYABLE_ERROR_PATTERNS)


def is_timeout_error(error: Optional[str]) -> bool:
    """Return True if the error indicates a read/write timeout."""
    if not error:
        return False
    lowered = error.lower()
    return "timed out" in lowered or "readtimeout" in lowered or "writetimeout" in lowered
