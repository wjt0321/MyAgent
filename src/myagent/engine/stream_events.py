"""Stream event types for MyAgent engine."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Any

from myagent.engine.messages import ConversationMessage


class StreamEvent(ABC):
    pass


@dataclass
class AssistantTextDelta(StreamEvent):
    text: str


@dataclass
class ToolExecutionStarted(StreamEvent):
    tool_name: str
    tool_use_id: str
    arguments: dict[str, Any]


@dataclass
class ToolExecutionCompleted(StreamEvent):
    tool_use_id: str
    result: str
    is_error: bool = False


@dataclass
class AssistantTurnComplete(StreamEvent):
    message: ConversationMessage


@dataclass
class StatusEvent(StreamEvent):
    message: str


@dataclass
class ErrorEvent(StreamEvent):
    error: Exception
    recoverable: bool = False


@dataclass
class CompactProgressEvent(StreamEvent):
    message: str


@dataclass
class PermissionRequestEvent(StreamEvent):
    """Event emitted when a tool execution needs user permission."""

    tool_name: str
    arguments: dict[str, Any]
    reason: str


@dataclass
class PermissionResultEvent(StreamEvent):
    """Event emitted after user responds to a permission request."""

    tool_name: str
    approved: bool
    reason: str
