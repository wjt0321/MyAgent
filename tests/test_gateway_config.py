"""Tests for gateway configuration."""

from __future__ import annotations

import os

import pytest

from myagent.gateway.config import (
    GatewayConfig,
    Platform,
    PlatformConfig,
    load_gateway_config,
)


class TestPlatformConfig:
    def test_default_creation(self):
        cfg = PlatformConfig()
        assert cfg.enabled is False
        assert cfg.token is None
        assert cfg.extra == {}

    def test_to_dict(self):
        cfg = PlatformConfig(enabled=True, token="secret", extra={"key": "val"})
        d = cfg.to_dict()
        assert d["enabled"] is True
        assert d["token"] == "secret"
        assert d["extra"] == {"key": "val"}

    def test_from_dict(self):
        d = {"enabled": True, "token": "secret", "extra": {"key": "val"}}
        cfg = PlatformConfig.from_dict(d)
        assert cfg.enabled is True
        assert cfg.token == "secret"
        assert cfg.extra == {"key": "val"}


class TestGatewayConfig:
    def test_default_creation(self):
        cfg = GatewayConfig()
        assert cfg.platforms == {}
        assert cfg.group_sessions_per_user is True

    def test_get_connected_platforms_empty(self):
        cfg = GatewayConfig()
        assert cfg.get_connected_platforms() == []

    def test_get_connected_platforms_with_token(self):
        cfg = GatewayConfig()
        cfg.platforms[Platform.TELEGRAM] = PlatformConfig(enabled=True, token="bot_token")
        connected = cfg.get_connected_platforms()
        assert Platform.TELEGRAM in connected

    def test_get_connected_platforms_disabled(self):
        cfg = GatewayConfig()
        cfg.platforms[Platform.TELEGRAM] = PlatformConfig(enabled=False, token="bot_token")
        connected = cfg.get_connected_platforms()
        assert Platform.TELEGRAM not in connected

    def test_to_dict_roundtrip(self):
        cfg = GatewayConfig()
        cfg.platforms[Platform.DISCORD] = PlatformConfig(enabled=True, token="discord_token")
        d = cfg.to_dict()
        cfg2 = GatewayConfig.from_dict(d)
        assert cfg2.platforms[Platform.DISCORD].enabled is True
        assert cfg2.platforms[Platform.DISCORD].token == "discord_token"


class TestLoadGatewayConfig:
    def test_load_empty(self, monkeypatch):
        # Clear env vars that might affect tests
        for key in list(os.environ.keys()):
            if key.endswith("_TOKEN") or key.endswith("_APP_ID"):
                monkeypatch.delenv(key, raising=False)
        cfg = load_gateway_config()
        assert isinstance(cfg, GatewayConfig)

    def test_telegram_from_env(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
        cfg = load_gateway_config()
        assert Platform.TELEGRAM in cfg.get_connected_platforms()
        assert cfg.platforms[Platform.TELEGRAM].token == "test_token_123"

    def test_discord_from_env(self, monkeypatch):
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "discord_secret")
        cfg = load_gateway_config()
        assert Platform.DISCORD in cfg.get_connected_platforms()

    def test_feishu_from_env(self, monkeypatch):
        monkeypatch.setenv("FEISHU_APP_ID", "app_123")
        monkeypatch.setenv("FEISHU_APP_SECRET", "secret_456")
        cfg = load_gateway_config()
        assert Platform.FEISHU in cfg.get_connected_platforms()
        assert cfg.platforms[Platform.FEISHU].extra.get("app_id") == "app_123"

    def test_weixin_from_env(self, monkeypatch):
        monkeypatch.setenv("WEIXIN_TOKEN", "wx_token")
        monkeypatch.setenv("WEIXIN_ACCOUNT_ID", "wx_account")
        cfg = load_gateway_config()
        assert Platform.WEIXIN in cfg.get_connected_platforms()

    def test_qq_from_env(self, monkeypatch):
        monkeypatch.setenv("QQ_APP_ID", "qq_app")
        monkeypatch.setenv("QQ_CLIENT_SECRET", "qq_secret")
        cfg = load_gateway_config()
        assert Platform.QQ in cfg.get_connected_platforms()
