"""Message types for MyAgent engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class TextBlock:
    text: str
    type: Literal["text"] = "text"


@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]
    type: Literal["tool_use"] = "tool_use"


@dataclass
class ToolResultBlock:
    tool_use_id: str
    content: str | list[TextBlock | ImageBlock]
    is_error: bool = False
    type: Literal["tool_result"] = "tool_result"


@dataclass
class ImageBlock:
    source: dict[str, Any]
    type: Literal["image"] = "image"


ContentBlock = TextBlock | ToolUseBlock | ToolResultBlock | ImageBlock


@dataclass
class ConversationMessage:
    role: Literal["system", "user", "assistant"]
    content: list[ContentBlock] = field(default_factory=list)

    @classmethod
    def from_user_text(cls, text: str) -> ConversationMessage:
        return cls(role="user", content=[TextBlock(text=text)])

    @classmethod
    def from_assistant_text(cls, text: str) -> ConversationMessage:
        return cls(role="assistant", content=[TextBlock(text=text)])

    @classmethod
    def from_system_text(cls, text: str) -> ConversationMessage:
        return cls(role="system", content=[TextBlock(text=text)])

    @property
    def text(self) -> str:
        parts = []
        for block in self.content:
            if isinstance(block, TextBlock):
                parts.append(block.text)
        return "\n".join(parts)

    @property
    def tool_uses(self) -> list[str]:
        return [block.id for block in self.content if isinstance(block, ToolUseBlock)]
