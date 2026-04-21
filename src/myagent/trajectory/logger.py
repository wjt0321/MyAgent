"""Trajectory logger for MyAgent."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class TrajectoryTurn:
    """A single turn in a conversation trajectory."""

    turn_number: int
    messages: list[dict[str, Any]]
    model: str
    completed: bool
    usage_tokens: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_number": self.turn_number,
            "messages": self.messages,
            "model": self.model,
            "completed": self.completed,
            "usage_tokens": self.usage_tokens,
            "timestamp": self.timestamp,
        }


class TrajectoryLogger:
    """Logs conversation trajectories for debugging and training data export."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path.home() / ".myagent" / "trajectories"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._turns: list[TrajectoryTurn] = []

    def log_turn(
        self,
        messages: list[dict[str, Any]],
        model: str,
        completed: bool,
        usage_tokens: int = 0,
    ) -> None:
        """Log a single conversation turn."""
        turn = TrajectoryTurn(
            turn_number=len(self._turns) + 1,
            messages=messages,
            model=model,
            completed=completed,
            usage_tokens=usage_tokens,
        )
        self._turns.append(turn)

    def save(self, session_id: str | None = None) -> Path:
        """Save the trajectory as JSON."""
        sid = session_id or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
        path = self.output_dir / f"trajectory-{sid}.json"

        data = {
            "session_id": sid,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "turns": [turn.to_dict() for turn in self._turns],
        }

        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def export_sharegpt(self, path: Path | None = None) -> Path:
        """Export trajectory in ShareGPT format for training."""
        if path is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            path = self.output_dir / f"sharegpt-{timestamp}.json"

        conversations: list[dict[str, str]] = []
        for turn in self._turns:
            for msg in turn.messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if isinstance(content, list):
                    content = json.dumps(content)

                if role == "user":
                    conversations.append({"from": "human", "value": content})
                elif role == "assistant":
                    conversations.append({"from": "gpt", "value": content})

        path.write_text(json.dumps(conversations, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the trajectory."""
        total_tokens = sum(turn.usage_tokens for turn in self._turns)
        completed = sum(1 for turn in self._turns if turn.completed)
        models = list(dict.fromkeys(turn.model for turn in self._turns))

        return {
            "total_turns": len(self._turns),
            "completed_turns": completed,
            "total_tokens": total_tokens,
            "models_used": models,
        }

    def clear(self) -> None:
        """Clear all logged turns."""
        self._turns = []
