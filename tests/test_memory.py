"""Tests for myagent memory system."""

from pathlib import Path

from myagent.memory.manager import MemoryEntry, MemoryManager, MemoryType


class TestMemoryManager:
    def test_memory_manager_creation(self, tmp_path: Path):
        manager = MemoryManager(memory_dir=tmp_path)
        assert manager.memory_dir == tmp_path

    def test_save_memory_entry(self, tmp_path: Path):
        manager = MemoryManager(memory_dir=tmp_path)
        entry = MemoryEntry(
            name="Test Title",
            description="测试描述",
            type=MemoryType.PROJECT,
            content="Test content here.",
        )
        saved_path = manager.save_memory(entry)

        assert saved_path.exists()
        assert "Test content here." in saved_path.read_text(encoding="utf-8")

    def test_list_memories(self, tmp_path: Path):
        manager = MemoryManager(memory_dir=tmp_path)
        manager.save_memory(
            MemoryEntry(
                name="Alpha",
                description="第一条",
                type=MemoryType.USER,
                content="Alpha content",
            )
        )
        manager.save_memory(
            MemoryEntry(
                name="Beta",
                description="第二条",
                type=MemoryType.FEEDBACK,
                content="Beta content",
            )
        )

        entries = manager.list_memories()
        assert len(entries) == 2
        titles = [e.name for e in entries]
        assert "Alpha" in titles
        assert "Beta" in titles

    def test_get_and_delete_memory(self, tmp_path: Path):
        manager = MemoryManager(memory_dir=tmp_path)
        manager.save_memory(
            MemoryEntry(
                name="Entry 1",
                description="待删除",
                type=MemoryType.PROJECT,
                content="Content 1",
            )
        )

        entry = manager.get_memory("Entry 1")
        assert entry is not None
        assert entry.name == "Entry 1"

        assert manager.delete_memory("Entry 1") is True
        assert manager.get_memory("Entry 1") is None

    def test_memory_entry_from_markdown(self):
        entry = MemoryEntry.from_markdown(
            """---
name: Test Title
description: Test description
type: reference
---

Test content.
""",
        )

        assert entry.name == "Test Title"
        assert entry.description == "Test description"
        assert entry.type is MemoryType.REFERENCE
        assert entry.content == "Test content."

    def test_load_memory_prompt(self, tmp_path: Path):
        manager = MemoryManager(memory_dir=tmp_path)
        manager.save_memory(
            MemoryEntry(
                name="Prompt Memory",
                description="用于提示词",
                type=MemoryType.USER,
                content="记住这一条信息。",
            )
        )

        prompt = manager.load_memory_prompt()
        assert prompt is not None
        assert "Prompt Memory" in prompt
        assert "记住这一条信息。" in prompt
