"""Tests for legacy Gateway adapters."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from myagent.gateway.adapter import GatewayAdapter, GatewayMessage
from myagent.gateway.manager import GatewayManager
from myagent.gateway.webhook import WebhookGateway


class TestGatewayMessage:
    def test_message_creation(self):
        msg = GatewayMessage(
            text="Hello",
            user_id="user-1",
            channel_id="channel-1",
            platform="test",
        )
        assert msg.text == "Hello"
        assert msg.user_id == "user-1"
        assert msg.platform == "test"

    def test_message_reply(self):
        msg = GatewayMessage(
            text="Hello",
            user_id="user-1",
            channel_id="channel-1",
            platform="test",
        )
        reply = msg.reply("Hi there!")
        assert reply.text == "Hi there!"
        assert reply.channel_id == msg.channel_id
        assert reply.platform == msg.platform


class TestWebhookGateway:
    @pytest.mark.asyncio
    async def test_webhook_creation(self):
        gw = WebhookGateway(host="0.0.0.0", port=8080)
        assert gw.name == "webhook"
        assert gw.host == "0.0.0.0"
        assert gw.port == 8080
        assert gw.running is False

    @pytest.mark.asyncio
    async def test_webhook_start_stop(self):
        gw = WebhookGateway(port=0)
        assert gw.running is False

        await gw.start()
        assert gw.running is True

        await gw.stop()
        assert gw.running is False

    @pytest.mark.asyncio
    async def test_webhook_receive_message(self):
        gw = WebhookGateway(port=0)
        messages = []

        async def handler(msg: GatewayMessage) -> None:
            messages.append(msg)

        gw.on_message(handler)
        await gw.start()

        await gw._handle_incoming(
            {"text": "Test message", "user_id": "u1", "channel_id": "c1"}
        )

        await gw.stop()

        assert len(messages) == 1
        assert messages[0].text == "Test message"

    @pytest.mark.asyncio
    async def test_webhook_send_message(self):
        gw = WebhookGateway(port=0)
        await gw.start()

        msg = GatewayMessage(text="Reply", user_id="u1", channel_id="c1", platform="webhook")
        await gw.send(msg)

        await gw.stop()


class TestLegacyGatewayManager:
    """Tests for the new GatewayManager (legacy compatibility)."""

    @pytest.mark.asyncio
    async def test_manager_creation(self):
        manager = GatewayManager()
        assert manager.adapters == {}

    @pytest.mark.asyncio
    async def test_register_adapter(self):
        from myagent.gateway.adapter_base import BasePlatformAdapter
        from myagent.gateway.base import Platform
        from myagent.gateway.config import PlatformConfig

        class TestAdapter(BasePlatformAdapter):
            async def connect(self) -> bool:
                return True
            async def disconnect(self) -> None:
                pass
            async def send(self, chat_id, content, reply_to=None, metadata=None):
                from myagent.gateway.base import SendResult
                return SendResult(success=True)
            async def get_chat_info(self, chat_id):
                return {}

        manager = GatewayManager()
        adapter = TestAdapter(PlatformConfig(), Platform.WEBHOOK)
        manager.register_adapter(adapter)
        assert len(manager.adapters) == 1

    @pytest.mark.asyncio
    async def test_start_all(self):
        from myagent.gateway.adapter_base import BasePlatformAdapter
        from myagent.gateway.base import Platform
        from myagent.gateway.config import PlatformConfig

        class TestAdapter(BasePlatformAdapter):
            async def connect(self) -> bool:
                self._running = True
                return True
            async def disconnect(self) -> None:
                self._running = False
            async def send(self, chat_id, content, reply_to=None, metadata=None):
                from myagent.gateway.base import SendResult
                return SendResult(success=True)
            async def get_chat_info(self, chat_id):
                return {}

        manager = GatewayManager()
        adapter = TestAdapter(PlatformConfig(), Platform.WEBHOOK)
        manager.register_adapter(adapter)

        await manager.start_all()
        assert adapter.is_connected is True

        await manager.stop_all()

    @pytest.mark.asyncio
    async def test_stop_all(self):
        from myagent.gateway.adapter_base import BasePlatformAdapter
        from myagent.gateway.base import Platform
        from myagent.gateway.config import PlatformConfig

        class TestAdapter(BasePlatformAdapter):
            async def connect(self) -> bool:
                self._running = True
                return True
            async def disconnect(self) -> None:
                self._running = False
            async def send(self, chat_id, content, reply_to=None, metadata=None):
                from myagent.gateway.base import SendResult
                return SendResult(success=True)
            async def get_chat_info(self, chat_id):
                return {}

        manager = GatewayManager()
        adapter = TestAdapter(PlatformConfig(), Platform.WEBHOOK)
        manager.register_adapter(adapter)

        await manager.start_all()
        await manager.stop_all()
        assert adapter.is_connected is False
