"""Tests for TUI QueryEngine integration."""

from __future__ import annotations

import pytest

from myagent.tui.app import MyAgentApp


class TestTUIQueryEngineIntegration:
    def test_app_has_query_engine(self):
        """App should initialize QueryEngine when provider is available."""
        app = MyAgentApp()
        assert app._query_engine is not None

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
