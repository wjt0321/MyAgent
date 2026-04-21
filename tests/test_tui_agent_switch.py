"""Tests for TUI agent switching functionality."""

from __future__ import annotations

import pytest

from myagent.tui.app import MyAgentApp


class TestAgentSwitching:
    def test_switch_agent_updates_query_engine_system_prompt(self):
        """Switching agent should update QueryEngine system prompt."""
        app = MyAgentApp()
        if app._query_engine is None:
            pytest.skip("No API key configured")

        original_prompt = app._query_engine.system_prompt
        app._switch_agent("explore")

        assert app._query_engine.system_prompt != original_prompt
        assert "exploration" in app._query_engine.system_prompt.lower()

    def test_explore_agent_limits_tools(self):
        """Explore agent should only have read-only tools."""
        app = MyAgentApp()
        if app._query_engine is None:
            pytest.skip("No API key configured")

        app._switch_agent("explore")
        tool_names = {t.name for t in app._query_engine.tool_registry.list_tools()}

        assert "Read" in tool_names
        assert "Glob" in tool_names
        assert "Grep" in tool_names
        assert "Write" not in tool_names
        assert "Edit" not in tool_names
        assert "Bash" not in tool_names

    def test_worker_agent_has_all_tools(self):
        """Worker agent should have all tools."""
        app = MyAgentApp()
        if app._query_engine is None:
            pytest.skip("No API key configured")

        app._switch_agent("worker")
        tool_names = {t.name for t in app._query_engine.tool_registry.list_tools()}

        assert "Read" in tool_names
        assert "Write" in tool_names
        assert "Edit" in tool_names
        assert "Bash" in tool_names

    def test_switch_to_invalid_agent_shows_error(self):
        """Switching to invalid agent should show error message."""
        app = MyAgentApp()
        app._switch_agent("nonexistent")

        assert app._transcript_lines[-1].startswith("[bold green]Agent:[/bold green]")
        assert "Unknown" in app._transcript_lines[-1]

    def test_switch_agent_clears_conversation(self):
        """Switching agent should reset conversation history."""
        app = MyAgentApp()
        if app._query_engine is None:
            pytest.skip("No API key configured")

        app._query_engine.messages.append(
            app._query_engine.messages[-1]
        )
        msg_count = len(app._query_engine.messages)

        app._switch_agent("explore")

        assert len(app._query_engine.messages) < msg_count
