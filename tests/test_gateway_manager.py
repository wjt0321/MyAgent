"""Tests for gateway manager."""

from __future__ import annotations

import pytest

from myagent.gateway.adapter_base import BasePlatformAdapter
from myagent.gateway.base import MessageEvent, Platform, SendResult, SessionSource
from myagent.gateway.config import PlatformConfig
from myagent.gateway.manager import GatewayManager


class MockAdapter(BasePlatformAdapter):
    """Mock adapter for testing."""

    def __init__(self, platform: Platform = Platform.TELEGRAM) -> None:
        super().__init__(PlatformConfig(enabled=True, token="test"), platform)
        self.sent_messages: list = []
        self.connected = False

    async def connect(self) -> bool:
        self.connected = True
        self._running = True
        return True

    async def disconnect(self) -> None:
        self.connected = False
        self._running = False

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: str | None = None,
        metadata: dict | None = None,
    ) -> SendResult:
        self.sent_messages.append({"chat_id": chat_id, "content": content})
        return SendResult(success=True)

    async def get_chat_info(self, chat_id: str) -> dict:
        return {"name": "Test", "type": "dm"}


class TestGatewayManager:
    def test_creation(self):
        mgr = GatewayManager()
        assert mgr.adapters == {}

    def test_register_adapter(self):
        mgr = GatewayManager()
        adapter = MockAdapter()
        mgr.register_adapter(adapter)
        assert Platform.TELEGRAM in mgr.adapters

    def test_get_adapter(self):
        mgr = GatewayManager()
        adapter = MockAdapter()
        mgr.register_adapter(adapter)
        assert mgr.get_adapter(Platform.TELEGRAM) is adapter
        assert mgr.get_adapter(Platform.DISCORD) is None

    @pytest.mark.asyncio
    async def test_start_all(self):
        mgr = GatewayManager()
        adapter = MockAdapter()
        mgr.register_adapter(adapter)
        await mgr.start_all()
        assert adapter.connected is True

    @pytest.mark.asyncio
    async def test_stop_all(self):
        mgr = GatewayManager()
        adapter = MockAdapter()
        mgr.register_adapter(adapter)
        await mgr.start_all()
        await mgr.stop_all()
        assert adapter.connected is False

    @pytest.mark.asyncio
    async def test_broadcast(self):
        mgr = GatewayManager()
        adapter = MockAdapter()
        mgr.register_adapter(adapter)
        await mgr.start_all()

        # Need home channel for broadcast
        from myagent.gateway.config import HomeChannel
        mgr.config.platforms[Platform.TELEGRAM] = PlatformConfig(
            enabled=True,
            home_channel=HomeChannel(platform=Platform.TELEGRAM, chat_id="123", name="Home"),
        )

        await mgr.broadcast("Hello!")
        assert len(adapter.sent_messages) == 1
        assert adapter.sent_messages[0]["content"] == "Hello!"

    def test_connected_platforms(self):
        mgr = GatewayManager()
        adapter = MockAdapter()
        mgr.register_adapter(adapter)
        assert mgr.connected_platforms == []

    @pytest.mark.asyncio
    async def test_message_handler_propagation(self):
        mgr = GatewayManager()
        adapter = MockAdapter()
        mgr.register_adapter(adapter)

        handler_calls = []

        async def handler(event):
            handler_calls.append(event)
            return "ok"

        mgr.set_message_handler(handler)
        assert adapter._message_handler is handler

    def test_create_from_config(self):
        from myagent.gateway.config import GatewayConfig, PlatformConfig
        config = GatewayConfig()
        config.platforms[Platform.TELEGRAM] = PlatformConfig(enabled=True, token="test")
        config.platforms[Platform.DISCORD] = PlatformConfig(enabled=True, token="test")

        mgr = GatewayManager(config)
        mgr.create_from_config()
        assert Platform.TELEGRAM in mgr.adapters
        assert Platform.DISCORD in mgr.adapters
