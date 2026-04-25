"""Tests for myagent CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from myagent.cli import app

runner = CliRunner()


class TestCLI:
    def test_cli_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "MyAgent" in result.output

    def test_cli_version(self):
        result = runner.invoke(app, ["main", "--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_init_quick_creates_base_config(self, monkeypatch, tmp_path: Path):
        monkeypatch.setenv("MYAGENT_HOME", str(tmp_path))

        result = runner.invoke(app, ["init", "--quick"])

        assert result.exit_code == 0
        assert (tmp_path / "config.yaml").exists()
        assert (tmp_path / "gateway.yaml").exists()
        assert (tmp_path / ".env").exists()
        assert "快速配置" in result.output

    def test_doctor_reports_next_steps_when_setup_incomplete(self, monkeypatch, tmp_path: Path):
        monkeypatch.setenv("MYAGENT_HOME", str(tmp_path))

        result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "myagent init --quick" in result.output
        assert "Setup Required" in result.output
