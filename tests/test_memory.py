"""Tests for myagent memory system."""

from pathlib import Path

import pytest

from myagent.memory.manager import MemoryEntry, MemoryManager


class TestMemoryManager:
    def test_memory_manager_creation(self, tmp_path: Path):
        manager = MemoryManager(memory_dir=tmp_path)
        assert manager.memory_dir == tmp_path

    def test_add_memory_entry(self, tmp_path: Path):
        manager = MemoryManager(memory_dir=tmp_path)
        entry = manager.add_entry("Test Title", "Test content here.")

        assert entry.title == "Test Title"
        assert entry.path.exists()
        assert "Test content here." in entry.path.read_text(encoding="utf-8")

    def test_add_entry_updates_index(self, tmp_path: Path):
        manager = MemoryManager(memory_dir=tmp_path)
        manager.add_entry("First", "Content 1")
        manager.add_entry("Second", "Content 2")

        index_path = tmp_path / "MEMORY.md"
        assert index_path.exists()
        index_content = index_path.read_text(encoding="utf-8")
        assert "First" in index_content
        assert "Second" in index_content

    def test_list_entries(self, tmp_path: Path):
        manager = MemoryManager(memory_dir=tmp_path)
        manager.add_entry("Alpha", "Alpha content")
        manager.add_entry("Beta", "Beta content")

        entries = manager.list_entries()
        assert len(entries) == 2
        titles = [e.title for e in entries]
        assert "Alpha" in titles
        assert "Beta" in titles

    def test_entry_file_format(self, tmp_path: Path):
        manager = MemoryManager(memory_dir=tmp_path)
        manager.add_entry("My Entry", "This is the content.")

        entries = manager.list_entries()
        assert len(entries) == 1

        content = entries[0].path.read_text(encoding="utf-8")
        assert "# My Entry" in content
        assert "This is the content." in content

    def test_memory_entry_from_file(self, tmp_path: Path):
        entry_file = tmp_path / "test-entry.md"
        entry_file.write_text("# Test Title\n\nTest content.\n", encoding="utf-8")

        entry = MemoryEntry.from_file(entry_file)
        assert entry.title == "Test Title"
        assert entry.path == entry_file

    def test_concurrent_add_safe(self, tmp_path: Path):
        manager = MemoryManager(memory_dir=tmp_path)
        manager.add_entry("Entry 1", "Content 1")
        manager.add_entry("Entry 2", "Content 2")

        entries = manager.list_entries()
        assert len(entries) == 2
