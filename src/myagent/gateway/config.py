"""Gateway configuration management.

Handles loading and validating configuration for all connected platforms.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from myagent.gateway.base import Platform

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _coerce_bool(value: Any, default: bool = True) -> bool:
    """Coerce bool-ish config values."""
    if value is None:
        return default
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "1", "yes", "on"):
            return True
        if lowered in ("false", "0", "no", "off"):
            return False
        return default
    return bool(value)


def _get_myagent_home() -> Path:
    """Get MyAgent home directory."""
    home = os.getenv("MYAGENT_HOME")
    if home:
        return Path(home)
    return Path.home() / ".myagent"


# ---------------------------------------------------------------------------
# Config classes
# ---------------------------------------------------------------------------

@dataclass
class HomeChannel:
    """Default destination for a platform."""

    platform: Platform
    chat_id: str
    name: str = "Home"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "chat_id": self.chat_id,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HomeChannel":
        return cls(
            platform=Platform(data["platform"]),
            chat_id=str(data["chat_id"]),
            name=data.get("name", "Home"),
        )


@dataclass
class SessionResetPolicy:
    """Controls when sessions reset (lose context)."""

    mode: str = "both"  # "daily", "idle", "both", or "none"
    at_hour: int = 4  # Hour for daily reset (0-23)
    idle_minutes: int = 1440  # 24 hours
    notify: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "at_hour": self.at_hour,
            "idle_minutes": self.idle_minutes,
            "notify": self.notify,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionResetPolicy":
        return cls(
            mode=data.get("mode") if data.get("mode") is not None else "both",
            at_hour=data.get("at_hour") if data.get("at_hour") is not None else 4,
            idle_minutes=data.get("idle_minutes") if data.get("idle_minutes") is not None else 1440,
            notify=data.get("notify") if data.get("notify") is not None else True,
        )


@dataclass
class PlatformConfig:
    """Configuration for a single messaging platform."""

    enabled: bool = False
    token: Optional[str] = None
    api_key: Optional[str] = None
    home_channel: Optional[HomeChannel] = None
    reply_to_mode: str = "first"  # "off", "first", "all"
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "enabled": self.enabled,
            "extra": self.extra,
            "reply_to_mode": self.reply_to_mode,
        }
        if self.token:
            result["token"] = self.token
        if self.api_key:
            result["api_key"] = self.api_key
        if self.home_channel:
            result["home_channel"] = self.home_channel.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlatformConfig":
        home_channel = None
        if "home_channel" in data:
            home_channel = HomeChannel.from_dict(data["home_channel"])
        return cls(
            enabled=data.get("enabled", False),
            token=data.get("token"),
            api_key=data.get("api_key"),
            home_channel=home_channel,
            reply_to_mode=data.get("reply_to_mode", "first"),
            extra=data.get("extra", {}),
        )


@dataclass
class StreamingConfig:
    """Configuration for real-time token streaming."""

    enabled: bool = False
    transport: str = "edit"  # "edit" or "off"
    edit_interval: float = 1.0
    buffer_threshold: int = 40
    cursor: str = " ▉"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "transport": self.transport,
            "edit_interval": self.edit_interval,
            "buffer_threshold": self.buffer_threshold,
            "cursor": self.cursor,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamingConfig":
        if not data:
            return cls()
        return cls(
            enabled=data.get("enabled", False),
            transport=data.get("transport", "edit"),
            edit_interval=float(data.get("edit_interval", 1.0)),
            buffer_threshold=int(data.get("buffer_threshold", 40)),
            cursor=data.get("cursor", " ▉"),
        )


@dataclass
class GatewayConfig:
    """Main gateway configuration."""

    platforms: Dict[Platform, PlatformConfig] = field(default_factory=dict)
    default_reset_policy: SessionResetPolicy = field(default_factory=SessionResetPolicy)
    reset_by_type: Dict[str, SessionResetPolicy] = field(default_factory=dict)
    reset_by_platform: Dict[Platform, SessionResetPolicy] = field(default_factory=dict)
    reset_triggers: List[str] = field(default_factory=lambda: ["/new", "/reset"])
    quick_commands: Dict[str, Any] = field(default_factory=dict)
    sessions_dir: Path = field(default_factory=lambda: _get_myagent_home() / "sessions")
    always_log_local: bool = True
    stt_enabled: bool = True
    group_sessions_per_user: bool = True
    thread_sessions_per_user: bool = False
    unauthorized_dm_behavior: str = "pair"
    streaming: StreamingConfig = field(default_factory=StreamingConfig)
    session_store_max_age_days: int = 90

    def get_connected_platforms(self) -> List[Platform]:
        """Return list of platforms that are enabled and configured."""
        connected = []
        for platform, config in self.platforms.items():
            if not config.enabled:
                continue
            # Token-based platforms
            if config.token or config.api_key:
                connected.append(platform)
            # Feishu uses app_id/app_secret
            elif platform == Platform.FEISHU and config.extra.get("app_id"):
                connected.append(platform)
            # WeCom uses bot_id/secret
            elif platform == Platform.WECOM and config.extra.get("bot_id"):
                connected.append(platform)
            # Weixin uses token + account_id
            elif platform == Platform.WEIXIN and (
                config.extra.get("account_id") or config.token
            ):
                connected.append(platform)
            # QQ uses app_id/client_secret
            elif platform == Platform.QQ and config.extra.get("app_id"):
                connected.append(platform)
            # DingTalk uses client_id/client_secret
            elif platform == Platform.DINGTALK and (
                config.extra.get("client_id") or os.getenv("DINGTALK_CLIENT_ID")
            ):
                connected.append(platform)
            # Webhook uses enabled flag only
            elif platform == Platform.WEBHOOK:
                connected.append(platform)
        return connected

    def get_home_channel(self, platform: Platform) -> Optional[HomeChannel]:
        """Get the home channel for a platform."""
        config = self.platforms.get(platform)
        if config:
            return config.home_channel
        return None

    def get_reset_policy(
        self,
        platform: Optional[Platform] = None,
        session_type: Optional[str] = None,
    ) -> SessionResetPolicy:
        """Get the appropriate reset policy."""
        if platform and platform in self.reset_by_platform:
            return self.reset_by_platform[platform]
        if session_type and session_type in self.reset_by_type:
            return self.reset_by_type[session_type]
        return self.default_reset_policy

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platforms": {
                p.value: c.to_dict() for p, c in self.platforms.items()
            },
            "default_reset_policy": self.default_reset_policy.to_dict(),
            "reset_by_type": {
                k: v.to_dict() for k, v in self.reset_by_type.items()
            },
            "reset_by_platform": {
                p.value: v.to_dict() for p, v in self.reset_by_platform.items()
            },
            "reset_triggers": self.reset_triggers,
            "quick_commands": self.quick_commands,
            "sessions_dir": str(self.sessions_dir),
            "always_log_local": self.always_log_local,
            "stt_enabled": self.stt_enabled,
            "group_sessions_per_user": self.group_sessions_per_user,
            "thread_sessions_per_user": self.thread_sessions_per_user,
            "unauthorized_dm_behavior": self.unauthorized_dm_behavior,
            "streaming": self.streaming.to_dict(),
            "session_store_max_age_days": self.session_store_max_age_days,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GatewayConfig":
        platforms = {}
        for platform_name, platform_data in data.get("platforms", {}).items():
            try:
                platform = Platform(platform_name)
                platforms[platform] = PlatformConfig.from_dict(platform_data)
            except ValueError:
                pass

        reset_by_type = {}
        for type_name, policy_data in data.get("reset_by_type", {}).items():
            reset_by_type[type_name] = SessionResetPolicy.from_dict(policy_data)

        reset_by_platform = {}
        for platform_name, policy_data in data.get("reset_by_platform", {}).items():
            try:
                platform = Platform(platform_name)
                reset_by_platform[platform] = SessionResetPolicy.from_dict(policy_data)
            except ValueError:
                pass

        default_policy = SessionResetPolicy()
        if "default_reset_policy" in data:
            default_policy = SessionResetPolicy.from_dict(data["default_reset_policy"])

        sessions_dir = _get_myagent_home() / "sessions"
        if "sessions_dir" in data:
            sessions_dir = Path(data["sessions_dir"])

        return cls(
            platforms=platforms,
            default_reset_policy=default_policy,
            reset_by_type=reset_by_type,
            reset_by_platform=reset_by_platform,
            reset_triggers=data.get("reset_triggers", ["/new", "/reset"]),
            quick_commands=data.get("quick_commands", {}),
            sessions_dir=sessions_dir,
            always_log_local=data.get("always_log_local", True),
            stt_enabled=_coerce_bool(data.get("stt_enabled"), True),
            group_sessions_per_user=_coerce_bool(data.get("group_sessions_per_user"), True),
            thread_sessions_per_user=_coerce_bool(data.get("thread_sessions_per_user"), False),
            unauthorized_dm_behavior=data.get("unauthorized_dm_behavior", "pair"),
            streaming=StreamingConfig.from_dict(data.get("streaming", {})),
            session_store_max_age_days=data.get("session_store_max_age_days", 90),
        )


# ---------------------------------------------------------------------------
# Environment variable loading
# ---------------------------------------------------------------------------

def _apply_env_overrides(config: GatewayConfig) -> None:
    """Apply environment variable overrides to config."""

    # Telegram
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if telegram_token:
        config.platforms.setdefault(Platform.TELEGRAM, PlatformConfig())
        config.platforms[Platform.TELEGRAM].enabled = True
        config.platforms[Platform.TELEGRAM].token = telegram_token

    # Discord
    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    if discord_token:
        config.platforms.setdefault(Platform.DISCORD, PlatformConfig())
        config.platforms[Platform.DISCORD].enabled = True
        config.platforms[Platform.DISCORD].token = discord_token

    # Slack
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    if slack_token:
        config.platforms.setdefault(Platform.SLACK, PlatformConfig())
        config.platforms[Platform.SLACK].enabled = True
        config.platforms[Platform.SLACK].token = slack_token

    # Feishu / Lark
    feishu_app_id = os.getenv("FEISHU_APP_ID")
    feishu_app_secret = os.getenv("FEISHU_APP_SECRET")
    if feishu_app_id and feishu_app_secret:
        config.platforms.setdefault(Platform.FEISHU, PlatformConfig())
        config.platforms[Platform.FEISHU].enabled = True
        config.platforms[Platform.FEISHU].extra.update({
            "app_id": feishu_app_id,
            "app_secret": feishu_app_secret,
            "domain": os.getenv("FEISHU_DOMAIN", "feishu"),
            "connection_mode": os.getenv("FEISHU_CONNECTION_MODE", "websocket"),
        })
        if os.getenv("FEISHU_ENCRYPT_KEY"):
            config.platforms[Platform.FEISHU].extra["encrypt_key"] = os.getenv("FEISHU_ENCRYPT_KEY")
        if os.getenv("FEISHU_VERIFICATION_TOKEN"):
            config.platforms[Platform.FEISHU].extra["verification_token"] = os.getenv("FEISHU_VERIFICATION_TOKEN")

    # Weixin (WeChat)
    weixin_token = os.getenv("WEIXIN_TOKEN")
    weixin_account_id = os.getenv("WEIXIN_ACCOUNT_ID")
    if weixin_token or weixin_account_id:
        config.platforms.setdefault(Platform.WEIXIN, PlatformConfig())
        config.platforms[Platform.WEIXIN].enabled = True
        if weixin_token:
            config.platforms[Platform.WEIXIN].token = weixin_token
        if weixin_account_id:
            config.platforms[Platform.WEIXIN].extra["account_id"] = weixin_account_id
        if os.getenv("WEIXIN_BASE_URL"):
            config.platforms[Platform.WEIXIN].extra["base_url"] = os.getenv("WEIXIN_BASE_URL").rstrip("/")

    # WeCom (Enterprise WeChat)
    wecom_bot_id = os.getenv("WECOM_BOT_ID")
    wecom_secret = os.getenv("WECOM_SECRET")
    if wecom_bot_id and wecom_secret:
        config.platforms.setdefault(Platform.WECOM, PlatformConfig())
        config.platforms[Platform.WECOM].enabled = True
        config.platforms[Platform.WECOM].extra.update({
            "bot_id": wecom_bot_id,
            "secret": wecom_secret,
        })

    # QQ
    qq_app_id = os.getenv("QQ_APP_ID")
    qq_client_secret = os.getenv("QQ_CLIENT_SECRET")
    if qq_app_id or qq_client_secret:
        config.platforms.setdefault(Platform.QQ, PlatformConfig())
        config.platforms[Platform.QQ].enabled = True
        if qq_app_id:
            config.platforms[Platform.QQ].extra["app_id"] = qq_app_id
        if qq_client_secret:
            config.platforms[Platform.QQ].extra["client_secret"] = qq_client_secret
        if os.getenv("QQ_ALLOWED_USERS"):
            config.platforms[Platform.QQ].extra["allow_from"] = os.getenv("QQ_ALLOWED_USERS")

    # DingTalk
    dingtalk_client_id = os.getenv("DINGTALK_CLIENT_ID")
    dingtalk_client_secret = os.getenv("DINGTALK_CLIENT_SECRET")
    if dingtalk_client_id and dingtalk_client_secret:
        config.platforms.setdefault(Platform.DINGTALK, PlatformConfig())
        config.platforms[Platform.DINGTALK].enabled = True
        config.platforms[Platform.DINGTALK].extra.update({
            "client_id": dingtalk_client_id,
            "client_secret": dingtalk_client_secret,
        })

    # Matrix
    matrix_token = os.getenv("MATRIX_ACCESS_TOKEN")
    if matrix_token:
        config.platforms.setdefault(Platform.MATRIX, PlatformConfig())
        config.platforms[Platform.MATRIX].enabled = True
        config.platforms[Platform.MATRIX].token = matrix_token
        if os.getenv("MATRIX_HOMESERVER"):
            config.platforms[Platform.MATRIX].extra["homeserver"] = os.getenv("MATRIX_HOMESERVER")

    # Webhook
    webhook_enabled = os.getenv("WEBHOOK_ENABLED", "").lower() in ("true", "1", "yes")
    if webhook_enabled:
        config.platforms.setdefault(Platform.WEBHOOK, PlatformConfig())
        config.platforms[Platform.WEBHOOK].enabled = True
        if os.getenv("WEBHOOK_PORT"):
            try:
                config.platforms[Platform.WEBHOOK].extra["port"] = int(os.getenv("WEBHOOK_PORT"))
            except ValueError:
                pass
        if os.getenv("WEBHOOK_SECRET"):
            config.platforms[Platform.WEBHOOK].extra["secret"] = os.getenv("WEBHOOK_SECRET")

    # Session settings
    idle_minutes = os.getenv("SESSION_IDLE_MINUTES")
    if idle_minutes:
        try:
            config.default_reset_policy.idle_minutes = int(idle_minutes)
        except ValueError:
            pass

    reset_hour = os.getenv("SESSION_RESET_HOUR")
    if reset_hour:
        try:
            config.default_reset_policy.at_hour = int(reset_hour)
        except ValueError:
            pass


def load_gateway_config() -> GatewayConfig:
    """Load gateway configuration from environment variables.

    Returns:
        GatewayConfig with all platform settings applied.
    """
    config = GatewayConfig()
    _apply_env_overrides(config)
    return config
