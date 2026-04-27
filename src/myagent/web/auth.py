"""Authentication for MyAgent Web UI.

Provides JWT-based authentication with optional password protection.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SECRET_KEY_PATH = Path.home() / ".myagent" / ".web_secret"
AUTH_CONFIG_PATH = Path.home() / ".myagent" / "auth.yaml"


try:
    import jwt

    JWT_AVAILABLE = True
except ImportError:
    jwt = None  # type: ignore[assignment]
    JWT_AVAILABLE = False


def _ensure_jwt() -> None:
    if not JWT_AVAILABLE:
        raise RuntimeError("PyJWT not installed. Run: pip install pyjwt")


def get_secret_key() -> str:
    """Get or generate JWT secret key."""
    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    key = secrets.token_urlsafe(32)
    SECRET_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SECRET_KEY_PATH.write_text(key)
    return key


def create_token(user_id: str, expires_days: int = 7) -> str:
    """Create JWT token for user."""
    _ensure_jwt()
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=expires_days),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, get_secret_key(), algorithm="HS256")  # type: ignore[union-attr]


def verify_token(token: str) -> str | None:
    """Verify JWT token and return user_id."""
    _ensure_jwt()
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=["HS256"])  # type: ignore[union-attr]
        return str(payload.get("user_id"))
    except jwt.ExpiredSignatureError:
        logger.debug("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug("JWT invalid token: %s", e)
        return None


class AuthConfig:
    """Simple auth configuration with optional password."""

    def __init__(self) -> None:
        self.password_hash: str | None = None
        self.enabled: bool = False
        self._load()

    def _load(self) -> None:
        if not AUTH_CONFIG_PATH.exists():
            return
        try:
            import yaml

            data = yaml.safe_load(AUTH_CONFIG_PATH.read_text(encoding="utf-8")) or {}
            self.password_hash = data.get("password_hash")
            self.enabled = bool(self.password_hash)
        except Exception as e:
            logger.error("Failed to load auth config: %s", e)

    def _save(self) -> None:
        try:
            import yaml

            data: dict[str, Any] = {}
            if self.password_hash:
                data["password_hash"] = self.password_hash
            AUTH_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            AUTH_CONFIG_PATH.write_text(
                yaml.dump(data, default_flow_style=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error("Failed to save auth config: %s", e)

    def set_password(self, password: str) -> None:
        """Set a new password."""
        import hashlib

        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
        self.password_hash = f"{salt}${pwd_hash}"
        self.enabled = True
        self._save()

    def verify_password(self, password: str) -> bool:
        """Verify a password."""
        if not self.password_hash:
            return True
        import hashlib

        if '$' not in self.password_hash:
            return hashlib.sha256(password.encode()).hexdigest() == self.password_hash
        salt, stored_hash = self.password_hash.split('$', 1)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
        return pwd_hash == stored_hash

    def disable(self) -> None:
        """Disable password protection."""
        self.password_hash = None
        self.enabled = False
        self._save()


# Global auth config instance
_auth_config: AuthConfig | None = None


def get_auth_config() -> AuthConfig:
    """Get the global auth config instance."""
    global _auth_config
    if _auth_config is None:
        _auth_config = AuthConfig()
    return _auth_config
