"""Tests for TUI memory integration."""

from __future__ import annotations

import pytest

from myagent.tui.app import MyAgentApp


class TestTUIMemoryIntegration:
    def test_app_has_memory_manager(self):
        """App should initialize a memory manager."""
        app = MyAgentApp()
        assert app._memory_manager is not None

    def test_memory_dir_created(self):
        """Memory directory should be created on init."""
        app = MyAgentApp()
        assert app._memory_manager.memory_dir.exists()

    def test_memory_command_lists_entries(self):
        """/memory command should list memory entries."""
        app = MyAgentApp()
        app._memory_manager.add_entry("Test Entry", "This is a test memory.")

        app._handle_command("/memory")

        assert any("Test Entry" in line for line in app._transcript_lines)
