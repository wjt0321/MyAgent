"""Session management for Web UI."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from myagent.engine.messages import ConversationMessage


@dataclass
class Session:
    """A chat session."""

    id: str
    agent: str
    model: str
    created_at: datetime
    updated_at: datetime
    messages: list[dict[str, Any]] = field(default_factory=list)
    user_id: str = "default"
    system_prompt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent": self.agent,
            "model": self.model,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": self.messages,
            "user_id": self.user_id,
            "system_prompt": self.system_prompt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        return cls(
            id=data["id"],
            agent=data["agent"],
            model=data["model"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            messages=data.get("messages", []),
            user_id=data.get("user_id", "default"),
            system_prompt=data.get("system_prompt", ""),
        )

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the session."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        self.updated_at = datetime.now()

    def save(self) -> None:
        """Persist session to disk via store."""
        # This is a convenience method; actual persistence is handled by SessionStore
        pass


class SessionStore:
    """In-memory session store with file persistence and user isolation."""

    def __init__(self, storage_dir: Path | None = None) -> None:
        self._sessions: dict[str, Session] = {}
        self._storage_dir = storage_dir or Path.home() / ".myagent" / "sessions"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._load_all()

    def create(self, agent: str = "general", model: str | None = None, user_id: str = "default") -> Session:
        """Create a new session."""
        if model is None:
            from myagent.config.settings import Settings
            settings = Settings.load()
            model = settings.model.default

        session = Session(
            id=str(uuid.uuid4())[:8],
            agent=agent,
            model=model,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=user_id,
        )
        self._sessions[session.id] = session
        self._save(session)
        return session

    def get(self, session_id: str, user_id: str | None = None) -> Session | None:
        """Get a session by ID, optionally filtering by user."""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if user_id is not None and session.user_id != user_id:
            return None
        return session

    def update(self, session: Session) -> None:
        """Update and persist an existing session."""
        self._sessions[session.id] = session
        self._save(session)

    def list_all(self, user_id: str | None = None) -> list[Session]:
        """List sessions, optionally filtered by user."""
        sessions = list(self._sessions.values())
        if user_id is not None:
            sessions = [s for s in sessions if s.user_id == user_id]
        return sorted(sessions, key=lambda s: s.updated_at, reverse=True)

    def delete(self, session_id: str, user_id: str | None = None) -> bool:
        """Delete a session, optionally checking user ownership."""
        session = self._sessions.get(session_id)
        if session is None:
            return False
        if user_id is not None and session.user_id != user_id:
            return False
        del self._sessions[session_id]
        file_path = self._storage_dir / f"{session_id}.yaml"
        if file_path.exists():
            file_path.unlink()
        return True

    def _save(self, session: Session) -> None:
        """Save a session to disk."""
        file_path = self._storage_dir / f"{session.id}.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(session.to_dict(), f, default_flow_style=False, allow_unicode=True)

    def _load_all(self) -> None:
        """Load all sessions from disk."""
        for file_path in self._storage_dir.glob("*.yaml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data:
                    session = Session.from_dict(data)
                    self._sessions[session.id] = session
            except Exception:
                continue
