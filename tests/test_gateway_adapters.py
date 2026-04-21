"""Tests for platform adapters."""

from __future__ import annotations

import pytest

from myagent.gateway.adapters.discord import DiscordAdapter
from myagent.gateway.adapters.feishu import FeishuAdapter
from myagent.gateway.adapters.qq import QQAdapter
from myagent.gateway.adapters.slack import SlackAdapter
from myagent.gateway.adapters.telegram import TelegramAdapter
from myagent.gateway.adapters.weixin import WeixinAdapter
from myagent.gateway.base import Platform, SendResult
from myagent.gateway.config import PlatformConfig


class TestFeishuAdapter:
    def test_creation(self):
        config = PlatformConfig(
            enabled=True,
            extra={"app_id": "test_id", "app_secret": "test_secret"},
        )
        adapter = FeishuAdapter(config)
        assert adapter.platform == Platform.FEISHU
        assert adapter.app_id == "test_id"
        assert adapter.api_base == "https://open.feishu.cn/open-apis"

    def test_lark_domain(self):
        config = PlatformConfig(
            enabled=True,
            extra={"app_id": "test", "app_secret": "test", "domain": "lark"},
        )
        adapter = FeishuAdapter(config)
        assert adapter.api_base == "https://open.larksuite.com/open-apis"

    def test_connect_without_deps(self):
        config = PlatformConfig(extra={"app_id": "test", "app_secret": "test"})
        adapter = FeishuAdapter(config)
        # Should fail gracefully without aiohttp
        result = asyncio_run(adapter.connect())
        assert result is False


class TestWeixinAdapter:
    def test_creation(self):
        config = PlatformConfig(
            enabled=True,
            token="wx_token",
            extra={"account_id": "acc123"},
        )
        adapter = WeixinAdapter(config)
        assert adapter.platform == Platform.WEIXIN
        assert adapter.token == "wx_token"


class TestQQAdapter:
    def test_creation(self):
        config = PlatformConfig(
            enabled=True,
            extra={"app_id": "qq_app", "client_secret": "qq_secret"},
        )
        adapter = QQAdapter(config)
        assert adapter.platform == Platform.QQ
        assert adapter.app_id == "qq_app"
        assert adapter.api_base == "https://api.sgroup.qq.com"

    def test_sandbox_mode(self):
        config = PlatformConfig(
            enabled=True,
            extra={"app_id": "qq_app", "client_secret": "qq_secret", "sandbox": True},
        )
        adapter = QQAdapter(config)
        assert adapter.api_base == "https://sandbox.api.sgroup.qq.com"

    def test_allowlist_parsing(self):
        config = PlatformConfig(
            extra={
                "app_id": "qq_app",
                "allow_from": "user1, user2, user3",
            },
        )
        adapter = QQAdapter(config)
        assert "user1" in adapter._allowed_users
        assert "user2" in adapter._allowed_users
        assert "user3" in adapter._allowed_users


class TestDiscordAdapter:
    def test_creation(self):
        config = PlatformConfig(enabled=True, token="discord_token")
        adapter = DiscordAdapter(config)
        assert adapter.platform == Platform.DISCORD
        assert adapter.token == "discord_token"


class TestSlackAdapter:
    def test_creation(self):
        config = PlatformConfig(enabled=True, token="slack_token")
        adapter = SlackAdapter(config)
        assert adapter.platform == Platform.SLACK
        assert adapter.token == "slack_token"


class TestTelegramAdapter:
    def test_creation(self):
        config = PlatformConfig(enabled=True, token="tg_token")
        adapter = TelegramAdapter(config)
        assert adapter.platform == Platform.TELEGRAM
        assert adapter.token == "tg_token"
        assert adapter.api_base == "https://api.telegram.org/bottg_token"


# Helper for running async in tests
def asyncio_run(coro):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)
