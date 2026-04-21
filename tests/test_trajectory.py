"""Tests for TrajectoryLogger."""

import json
from pathlib import Path

import pytest

from myagent.trajectory.logger import TrajectoryLogger, TrajectoryTurn


class TestTrajectoryTurn:
    def test_turn_creation(self):
        turn = TrajectoryTurn(
            turn_number=1,
            messages=[{"role": "user", "content": "hello"}],
            model="gpt-4o",
            completed=True,
        )
        assert turn.turn_number == 1
        assert turn.model == "gpt-4o"
        assert turn.completed is True

    def test_turn_to_dict(self):
        turn = TrajectoryTurn(
            turn_number=2,
            messages=[{"role": "assistant", "content": "hi"}],
            model="claude-sonnet",
            completed=False,
            usage_tokens=150,
        )
        data = turn.to_dict()
        assert data["turn_number"] == 2
        assert data["model"] == "claude-sonnet"
        assert data["completed"] is False
        assert data["usage_tokens"] == 150


class TestTrajectoryLogger:
    def test_logger_creation(self, tmp_path: Path):
        logger = TrajectoryLogger(output_dir=tmp_path)
        assert logger.output_dir == tmp_path
        assert logger._turns == []

    def test_log_turn(self, tmp_path: Path):
        logger = TrajectoryLogger(output_dir=tmp_path)
        logger.log_turn(
            messages=[{"role": "user", "content": "test"}],
            model="gpt-4o",
            completed=True,
        )
        assert len(logger._turns) == 1
        assert logger._turns[0].turn_number == 1
        assert logger._turns[0].model == "gpt-4o"

    def test_log_multiple_turns(self, tmp_path: Path):
        logger = TrajectoryLogger(output_dir=tmp_path)
        logger.log_turn([{"role": "user", "content": "q1"}], "gpt-4o", True)
        logger.log_turn([{"role": "user", "content": "q2"}], "gpt-4o", True)
        logger.log_turn([{"role": "user", "content": "q3"}], "claude", False)

        assert len(logger._turns) == 3
        assert logger._turns[2].turn_number == 3
        assert logger._turns[2].completed is False

    def test_save_trajectory(self, tmp_path: Path):
        logger = TrajectoryLogger(output_dir=tmp_path)
        logger.log_turn(
            messages=[{"role": "user", "content": "hello"}],
            model="gpt-4o",
            completed=True,
        )

        path = logger.save(session_id="test-session")
        assert path.exists()

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["session_id"] == "test-session"
        assert len(data["turns"]) == 1
        assert data["turns"][0]["model"] == "gpt-4o"

    def test_save_auto_session_id(self, tmp_path: Path):
        logger = TrajectoryLogger(output_dir=tmp_path)
        logger.log_turn([{"role": "user", "content": "test"}], "gpt-4o", True)

        path = logger.save()
        assert path.exists()

        data = json.loads(path.read_text(encoding="utf-8"))
        assert "session_id" in data
        assert len(data["session_id"]) > 0

    def test_export_sharegpt(self, tmp_path: Path):
        logger = TrajectoryLogger(output_dir=tmp_path)
        logger.log_turn(
            messages=[
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a programming language."},
            ],
            model="gpt-4o",
            completed=True,
        )

        path = logger.export_sharegpt()
        assert path.exists()

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data[0]["from"] == "human"
        assert data[0]["value"] == "What is Python?"
        assert data[1]["from"] == "gpt"
        assert data[1]["value"] == "Python is a programming language."

    def test_export_sharegpt_empty(self, tmp_path: Path):
        logger = TrajectoryLogger(output_dir=tmp_path)
        path = logger.export_sharegpt()
        assert path.exists()

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data == []

    def test_clear(self, tmp_path: Path):
        logger = TrajectoryLogger(output_dir=tmp_path)
        logger.log_turn([{"role": "user", "content": "test"}], "gpt-4o", True)
        logger.clear()

        assert len(logger._turns) == 0

    def test_get_summary(self, tmp_path: Path):
        logger = TrajectoryLogger(output_dir=tmp_path)
        logger.log_turn([{"role": "user", "content": "q1"}], "gpt-4o", True, usage_tokens=100)
        logger.log_turn([{"role": "user", "content": "q2"}], "gpt-4o", False, usage_tokens=50)

        summary = logger.get_summary()
        assert summary["total_turns"] == 2
        assert summary["completed_turns"] == 1
        assert summary["total_tokens"] == 150
        assert summary["models_used"] == ["gpt-4o"]
