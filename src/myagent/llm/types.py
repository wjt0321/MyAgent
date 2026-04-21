"""Stream chunk types for LLM providers."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Any


class StreamChunk(ABC):
    """Base class for all stream chunks."""


@dataclass
class TextChunk(StreamChunk):
    """A chunk of text from the assistant."""

    text: str


@dataclass
class ToolUseChunk(StreamChunk):
    """A tool use request from the assistant."""

    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolResultChunk(StreamChunk):
    """A tool result to send back to the model."""

    tool_use_id: str
    content: str
    is_error: bool = False


@dataclass
class DoneChunk(StreamChunk):
    """Signifies the end of the stream."""
