"""Tests for setup readiness detection."""

from __future__ import annotations

from pathlib import Path

import yaml

from myagent.init.status import get_setup_status


def test_setup_status_detects_missing_workspace_and_llm(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MYAGENT_HOME", str(tmp_path))

    status = get_setup_status(home=tmp_path)

    assert status.overall_ready is False
    assert status.workspace_ready is False
    assert status.llm_ready is False
    assert status.next_action == "myagent init --quick"


def test_setup_status_detects_ready_basic_setup(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MYAGENT_HOME", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret-value")

    (tmp_path / "workspace").mkdir(parents=True)
    (tmp_path / "memory").mkdir()
    (tmp_path / "projects").mkdir()
    (tmp_path / "sessions").mkdir()
    (tmp_path / "logs").mkdir()
    (tmp_path / "config.yaml").write_text(
        yaml.safe_dump({"model": {"default": "anthropic/claude-sonnet-4"}}),
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=secret-value\n", encoding="utf-8")

    status = get_setup_status(home=tmp_path)

    assert status.overall_ready is True
    assert status.workspace_ready is True
    assert status.config_ready is True
    assert status.llm_ready is True
    assert status.next_action == "myagent --tui"
