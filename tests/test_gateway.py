"""Tests for Gateway adapters."""

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


class TestGatewayManager:
    @pytest.mark.asyncio
    async def test_manager_creation(self):
        manager = GatewayManager()
        assert manager.adapters == []

    @pytest.mark.asyncio
    async def test_register_adapter(self):
        manager = GatewayManager()
        gw = WebhookGateway(port=0)
        manager.register(gw)
        assert len(manager.adapters) == 1

    @pytest.mark.asyncio
    async def test_start_all(self):
        manager = GatewayManager()
        gw = WebhookGateway(port=0)
        manager.register(gw)

        await manager.start_all()
        assert gw.running is True

        await manager.stop_all()

    @pytest.mark.asyncio
    async def test_stop_all(self):
        manager = GatewayManager()
        gw = WebhookGateway(port=0)
        manager.register(gw)

        await manager.start_all()
        await manager.stop_all()
        assert gw.running is False

    @pytest.mark.asyncio
    async def test_broadcast(self):
        manager = GatewayManager()
        gw = WebhookGateway(port=0)
        manager.register(gw)

        await manager.start_all()

        msg = GatewayMessage(text="Broadcast", user_id="bot", channel_id="all", platform="webhook")
        await manager.broadcast(msg)

        await manager.stop_all()

    @pytest.mark.asyncio
    async def test_on_message_handler(self):
        manager = GatewayManager()
        gw = WebhookGateway(port=0)
        manager.register(gw)

        received = []

        async def handler(msg: GatewayMessage) -> None:
            received.append(msg)

        manager.on_message(handler)
        await manager.start_all()

        await gw._handle_incoming(
            {"text": "Hello", "user_id": "u1", "channel_id": "c1"}
        )

        await manager.stop_all()

        assert len(received) == 1
        assert received[0].text == "Hello"
