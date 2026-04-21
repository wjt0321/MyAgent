"""Tests for TUI screens."""

from __future__ import annotations

import pytest
from textual.widgets import Button, Label, Static

from myagent.tui.screens import PermissionModalScreen


class TestPermissionModalScreen:
    def test_screen_creation(self):
        """Permission modal should be created with tool info."""
        screen = PermissionModalScreen(
            tool_name="Bash",
            arguments={"command": "ls -la"},
            reason="Bash command requires approval",
        )
        assert screen.tool_name == "Bash"
        assert screen.arguments == {"command": "ls -la"}
        assert screen.reason == "Bash command requires approval"

    def test_screen_arguments_storage(self):
        """Screen should store arguments correctly."""
        screen = PermissionModalScreen(
            tool_name="Write",
            arguments={"path": "test.txt", "content": "hello"},
            reason="Write tool requires approval",
        )
        assert screen.arguments["path"] == "test.txt"
        assert screen.arguments["content"] == "hello"
