"""Memory management system.

Handles persistent memory storage, retrieval, and indexing.
Inspired by Claude Code's memdir system.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class MemoryType(Enum):
    """Types of persistent memory."""
    USER = "user"
    FEEDBACK = "feedback"
    PROJECT = "project"
    REFERENCE = "reference"


@dataclass
class MemoryEntry:
    """A single memory entry."""
    name: str
    description: str
    type: MemoryType
    content: str
    path: Path | None = None

    def to_markdown(self) -> str:
        """Convert to markdown with frontmatter."""
        return f"""---
name: {self.name}
description: {self.description}
type: {self.type.value}
---

{self.content}
"""

    @classmethod
    def from_markdown(cls, text: str, path: Path | None = None) -> MemoryEntry:
        """Parse memory from markdown with frontmatter."""
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n+(.*)$', text, re.DOTALL)
        if not frontmatter_match:
            return cls(
                name="Unknown",
                description="",
                type=MemoryType.USER,
                content=text.strip(),
                path=path,
            )

        frontmatter = frontmatter_match.group(1)
        content = frontmatter_match.group(2).strip()

        # Parse frontmatter fields
        fields: dict[str, str] = {}
        for line in frontmatter.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                fields[key.strip()] = value.strip()

        return cls(
            name=fields.get('name', 'Unknown'),
            description=fields.get('description', ''),
            type=MemoryType(fields.get('type', 'user')),
            content=content,
            path=path,
        )


class MemoryManager:
    """Manages persistent memories."""

    def __init__(self, memory_dir: Path) -> None:
        self.memory_dir = Path(memory_dir)
        self.index_path = self.memory_dir / "MEMORY.md"

    def ensure(self) -> None:
        """Ensure memory directory exists."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def list_memories(self) -> list[MemoryEntry]:
        """List all memory entries."""
        if not self.memory_dir.exists():
            return []

        entries = []
        for path in sorted(self.memory_dir.glob("*.md")):
            if path.name == "MEMORY.md":
                continue
            try:
                text = path.read_text(encoding="utf-8")
                entry = MemoryEntry.from_markdown(text, path)
                entries.append(entry)
            except Exception:
                continue
        return entries

    def get_memory(self, name: str) -> MemoryEntry | None:
        """Get a memory by name."""
        for entry in self.list_memories():
            if entry.name == name:
                return entry
        return None

    def save_memory(self, entry: MemoryEntry) -> Path:
        """Save a memory entry."""
        self.ensure()

        # Generate filename from name
        slug = re.sub(r'[^a-zA-Z0-9]+', '_', entry.name.strip().lower()).strip('_') or "memory"
        path = self.memory_dir / f"{slug}.md"

        # Write memory file
        path.write_text(entry.to_markdown(), encoding="utf-8")

        # Update index
        self._update_index(entry, path.name)

        return path

    def delete_memory(self, name: str) -> bool:
        """Delete a memory by name."""
        entry = self.get_memory(name)
        if not entry or not entry.path:
            return False

        entry.path.unlink(missing_ok=True)
        self._rebuild_index()
        return True

    def load_memory_prompt(self, max_entries: int = 5) -> str | None:
        """Generate a prompt section with memories."""
        entries = self.list_memories()[:max_entries]
        if not entries:
            return None

        lines = ["# Memory System", ""]
        for entry in entries:
            lines.extend([
                f"## {entry.name}",
                f"*{entry.description}*",
                "",
                entry.content[:2000],
                "",
            ])

        return "\n".join(lines)

    def _update_index(self, entry: MemoryEntry, filename: str) -> None:
        """Update MEMORY.md index with a new entry."""
        if not self.index_path.exists():
            return

        content = self.index_path.read_text(encoding="utf-8")
        link = f"- [{entry.name}]({filename}) — {entry.description}"

        if filename not in content:
            content = content.rstrip() + f"\n{link}\n"
            self.index_path.write_text(content, encoding="utf-8")

    def _rebuild_index(self) -> None:
        """Rebuild MEMORY.md index from all memory files."""
        if not self.index_path.exists():
            return

        entries = self.list_memories()
        lines = ["# Memory Index", ""]

        for entry in entries:
            if entry.path:
                lines.append(f"- [{entry.name}]({entry.path.name}) — {entry.description}")

        self.index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
