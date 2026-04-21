"""Memory management for MyAgent."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class MemoryEntry:
    """A single memory entry."""

    title: str
    path: Path

    @classmethod
    def from_file(cls, path: Path) -> MemoryEntry:
        """Load a memory entry from a file."""
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        title = path.stem
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip()
        return cls(title=title, path=path)


class MemoryManager:
    """Manages persistent memory entries as Markdown files."""

    def __init__(self, memory_dir: Path) -> None:
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def add_entry(self, title: str, content: str) -> MemoryEntry:
        """Add a new memory entry."""
        safe_title = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title)
        safe_title = safe_title.replace(" ", "-").lower()

        entry_path = self.memory_dir / f"{safe_title}.md"

        entry_content = f"# {title}\n\n{content}\n"
        entry_path.write_text(entry_content, encoding="utf-8")

        self._update_index()

        return MemoryEntry(title=title, path=entry_path)

    def list_entries(self) -> list[MemoryEntry]:
        """List all memory entries."""
        entries = []
        for path in sorted(self.memory_dir.glob("*.md")):
            if path.name == "MEMORY.md":
                continue
            try:
                entries.append(MemoryEntry.from_file(path))
            except Exception:
                continue
        return entries

    def _update_index(self) -> None:
        """Update the MEMORY.md index file."""
        with self._lock:
            entries = self.list_entries()
            lines = ["# Memory Index\n", f"\nUpdated: {datetime.now().isoformat()}\n\n"]

            for entry in entries:
                rel_path = entry.path.name
                lines.append(f"- [{entry.title}]({rel_path})\n")

            index_path = self.memory_dir / "MEMORY.md"
            index_path.write_text("".join(lines), encoding="utf-8")
