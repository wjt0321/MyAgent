"""Tests for myagent CLI."""

from typer.testing import CliRunner

from myagent.cli import app


runner = CliRunner()


class TestCLI:
    def test_cli_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "MyAgent" in result.output

    def test_cli_version(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
