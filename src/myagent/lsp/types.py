"""LSP types for MyAgent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LSPPosition:
    """Position in a text document."""

    line: int
    character: int

    def to_dict(self) -> dict[str, int]:
        return {"line": self.line, "character": self.character}


@dataclass
class LSPRange:
    """Range in a text document."""

    start: LSPPosition
    end: LSPPosition

    def to_dict(self) -> dict[str, dict[str, int]]:
        return {"start": self.start.to_dict(), "end": self.end.to_dict()}


@dataclass
class Diagnostic:
    """LSP diagnostic item."""

    range: LSPRange
    message: str
    severity: int | None = None
    code: str | None = None
    source: str | None = None


@dataclass
class TextDocumentItem:
    """Text document item for LSP."""

    uri: str
    language_id: str
    version: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "languageId": self.language_id,
            "version": self.version,
            "text": self.text,
        }
