"""Tests for TUI QueryEngine integration."""

from __future__ import annotations

from myagent.tui.app import MyAgentApp


class TestTUIQueryEngineIntegration:
    def test_app_has_query_engine_or_setup_required_state(self):
        """App should initialize QueryEngine or enter setup-required state."""
        app = MyAgentApp()
        assert app._query_engine is not None or app.setup_status.overall_ready is False

    def test_app_has_tool_registry(self):
        """App should have a tool registry with tools."""
        app = MyAgentApp()
        assert app._tool_registry is not None
        tools = app._tool_registry.list_tools()
        assert len(tools) > 0

    def test_app_has_permission_checker(self):
        """App should have a permission checker."""
        app = MyAgentApp()
        assert app._permission_checker is not None

    def test_app_has_cost_tracker(self):
        """App should have a cost tracker."""
        app = MyAgentApp()
        assert app._cost_tracker is not None

    def test_tool_registry_has_core_tools(self):
        """Tool registry should have core tools."""
        app = MyAgentApp()
        tool_names = {t.name for t in app._tool_registry.list_tools()}
        assert "Read" in tool_names
        assert "Bash" in tool_names
        assert "Glob" in tool_names
        assert "Grep" in tool_names

    def test_tool_call_updates_activity_state(self):
        """Tool call should update structured activity state."""
        app = MyAgentApp()

        app.add_tool_call("Read", {"path": "README.md"}, tool_use_id="tool-1")

        assert app._activity_state["tool_name"] == "Read"
        assert app._activity_state["tool_use_id"] == "tool-1"
        assert app._activity_state["status"] == "running"
