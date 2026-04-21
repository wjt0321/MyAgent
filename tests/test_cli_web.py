"""Tests for CLI web command."""

from __future__ import annotations

from typer.testing import CliRunner

from myagent.cli import app

runner = CliRunner()


class TestCLIWebCommand:
    def test_web_command_exists(self):
        """Web command should be available in CLI."""
        result = runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0
        assert "Web UI" in result.output

    def test_web_command_default_options(self):
        """Web command should show default options."""
        result = runner.invoke(app, ["web", "--help"])
        assert "127.0.0.1" in result.output
        assert "8000" in result.output
