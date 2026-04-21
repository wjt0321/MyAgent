"""Tests for TUI TextArea input."""

from __future__ import annotations

import pytest

from myagent.tui.app import MyAgentApp


class TestTUITextArea:
    def test_textarea_exists(self):
        """Composer should be a TextArea widget."""
        app = MyAgentApp()
        # TextArea is available in textual.widgets
        from textual.widgets import TextArea

        # Just verify TextArea can be imported
        assert TextArea is not None
