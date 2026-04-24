"""Gateway session persistence for MyAgent.

Manages user-to-session mappings across platform adapters with
file-based persistence for recovery after restarts.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from myagent.gateway.base import Platform
from myagent.gateway.config import _get_myagent_home

logger = logging.getLogger(__name__)


class GatewaySessionStore:
    """Persistent store for gateway user-session mappings.

    Maps user identifiers (platform-specific) to session IDs so that
    users maintain continuity across restarts.
    """

    def __init__(self, storage_path: Path | None = None) -> None:
        self._storage_path = storage_path or _get_myagent_home() / "gateway_sessions.yaml"
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        # user_key -> session_id mapping
        self._user_sessions: Dict[str, str] = {}
        # session_id -> metadata mapping
        self._session_meta: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _user_key(self, platform: Platform, user_id: str, chat_id: str) -> str:
        """Build a unique key for a user across platforms."""
        return f"{platform.value}:{chat_id}:{user_id}"

    def get_session_id(
        self, platform: Platform, user_id: str, chat_id: str
    ) -> str | None:
        """Get the stored session ID for a user, if any."""
        key = self._user_key(platform, user_id, chat_id)
        return self._user_sessions.get(key)

    def bind_session(
        self,
        platform: Platform,
        user_id: str,
        chat_id: str,
        session_id: str,
        agent: str = "general",
    ) -> None:
        """Bind a user to a session ID and persist."""
        key = self._user_key(platform, user_id, chat_id)
        self._user_sessions[key] = session_id
        self._session_meta[session_id] = {
            "platform": platform.value,
            "user_id": user_id,
            "chat_id": chat_id,
            "agent": agent,
        }
        self._save()
        logger.debug("Bound session %s to user %s", session_id, key)

    def unbind_session(
        self, platform: Platform, user_id: str, chat_id: str
    ) -> None:
        """Remove a user-session binding."""
        key = self._user_key(platform, user_id, chat_id)
        session_id = self._user_sessions.pop(key, None)
        if session_id:
            self._session_meta.pop(session_id, None)
            self._save()
            logger.debug("Unbound session for user %s", key)

    def get_session_meta(self, session_id: str) -> Dict[str, Any] | None:
        """Get metadata for a session."""
        return self._session_meta.get(session_id)

    def update_session_meta(self, session_id: str, **kwargs: Any) -> None:
        """Update metadata for a session."""
        if session_id in self._session_meta:
            self._session_meta[session_id].update(kwargs)
            self._save()

    def list_bindings(self) -> Dict[str, str]:
        """Return a copy of all user-session bindings."""
        return dict(self._user_sessions)

    def clear(self) -> None:
        """Clear all bindings and persist."""
        self._user_sessions.clear()
        self._session_meta.clear()
        self._save()

    def _load(self) -> None:
        """Load bindings from disk."""
        if not self._storage_path.exists():
            return
        try:
            data = yaml.safe_load(self._storage_path.read_text(encoding="utf-8"))
            if not data:
                return
            self._user_sessions = data.get("user_sessions", {})
            self._session_meta = data.get("session_meta", {})
            logger.info(
                "Loaded %d gateway session bindings",
                len(self._user_sessions),
            )
        except Exception as e:
            logger.error("Failed to load gateway sessions: %s", e)
            self._user_sessions = {}
            self._session_meta = {}

    def _save(self) -> None:
        """Save bindings to disk."""
        try:
            data = {
                "user_sessions": self._user_sessions,
                "session_meta": self._session_meta,
            }
            self._storage_path.write_text(
                yaml.dump(data, default_flow_style=False, allow_unicode=True),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error("Failed to save gateway sessions: %s", e)
