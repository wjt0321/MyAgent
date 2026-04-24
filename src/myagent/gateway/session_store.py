"""Gateway session persistence for MyAgent.

Manages user-to-session mappings across platform adapters with
file-based persistence for recovery after restarts.
Supports LRU eviction and TTL expiration.
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
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
    Features LRU eviction and TTL expiration for memory management.
    """

    DEFAULT_MAX_SESSIONS = 1000
    DEFAULT_TTL_SECONDS = 7 * 24 * 3600  # 7 days

    def __init__(
        self,
        storage_path: Path | None = None,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        self._storage_path = storage_path or _get_myagent_home() / "gateway_sessions.yaml"
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._max_sessions = max_sessions
        self._ttl_seconds = ttl_seconds
        # user_key -> (session_id, last_access_time) mapping (OrderedDict for LRU)
        self._user_sessions: OrderedDict[str, tuple[str, float]] = OrderedDict()
        # session_id -> metadata mapping
        self._session_meta: Dict[str, Dict[str, Any]] = {}
        self._load()
        self._evict_expired()

    def _user_key(self, platform: Platform, user_id: str, chat_id: str) -> str:
        """Build a unique key for a user across platforms."""
        return f"{platform.value}:{chat_id}:{user_id}"

    def _evict_expired(self) -> None:
        """Remove sessions that have exceeded TTL."""
        now = time.time()
        expired_keys = [
            key for key, (_, last_access) in self._user_sessions.items()
            if now - last_access > self._ttl_seconds
        ]
        for key in expired_keys:
            session_id, _ = self._user_sessions.pop(key)
            self._session_meta.pop(session_id, None)
            logger.debug("Evicted expired session %s", session_id)
        if expired_keys:
            self._save()

    def _evict_lru(self) -> None:
        """Evict least recently used session when at capacity."""
        while len(self._user_sessions) >= self._max_sessions:
            key, (session_id, _) = self._user_sessions.popitem(last=False)
            self._session_meta.pop(session_id, None)
            logger.debug("Evicted LRU session %s", session_id)

    def get_session_id(
        self, platform: Platform, user_id: str, chat_id: str
    ) -> str | None:
        """Get the stored session ID for a user, if any."""
        key = self._user_key(platform, user_id, chat_id)
        entry = self._user_sessions.get(key)
        if entry is None:
            return None
        session_id, last_access = entry
        # Check TTL
        if time.time() - last_access > self._ttl_seconds:
            self._user_sessions.pop(key, None)
            self._session_meta.pop(session_id, None)
            self._save()
            return None
        # Update LRU order
        self._user_sessions.move_to_end(key)
        self._user_sessions[key] = (session_id, time.time())
        return session_id

    def bind_session(
        self,
        platform: Platform,
        user_id: str,
        chat_id: str,
        session_id: str,
        agent: str = "general",
    ) -> None:
        """Bind a user to a session ID and persist."""
        self._evict_expired()
        if len(self._user_sessions) >= self._max_sessions:
            self._evict_lru()

        key = self._user_key(platform, user_id, chat_id)
        self._user_sessions[key] = (session_id, time.time())
        self._user_sessions.move_to_end(key)
        self._session_meta[session_id] = {
            "platform": platform.value,
            "user_id": user_id,
            "chat_id": chat_id,
            "agent": agent,
            "created_at": time.time(),
        }
        self._save()
        logger.debug("Bound session %s to user %s", session_id, key)

    def unbind_session(
        self, platform: Platform, user_id: str, chat_id: str
    ) -> None:
        """Remove a user-session binding."""
        key = self._user_key(platform, user_id, chat_id)
        entry = self._user_sessions.pop(key, None)
        if entry:
            session_id, _ = entry
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
        return {k: v[0] for k, v in self._user_sessions.items()}

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
            # Handle legacy format (session_id only) and new format (session_id, timestamp)
            raw_sessions = data.get("user_sessions", {})
            self._user_sessions = OrderedDict()
            for key, value in raw_sessions.items():
                if isinstance(value, tuple) and len(value) == 2:
                    self._user_sessions[key] = value
                else:
                    # Legacy format: just session_id
                    self._user_sessions[key] = (value, time.time())
            self._session_meta = data.get("session_meta", {})
            logger.info(
                "Loaded %d gateway session bindings",
                len(self._user_sessions),
            )
        except Exception as e:
            logger.error("Failed to load gateway sessions: %s", e)
            self._user_sessions = OrderedDict()
            self._session_meta = {}

    def _save(self) -> None:
        """Save bindings to disk."""
        try:
            data = {
                "user_sessions": dict(self._user_sessions),
                "session_meta": self._session_meta,
            }
            self._storage_path.write_text(
                yaml.dump(data, default_flow_style=False, allow_unicode=True),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error("Failed to save gateway sessions: %s", e)
