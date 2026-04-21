"""Tests for RemoteBridge."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from myagent.remote.bridge import RemoteBridge, RemoteMessage


class TestRemoteMessage:
    def test_message_creation(self):
        msg = RemoteMessage(
            type="request",
            payload={"action": "run_task"},
            sender="client-1",
        )
        assert msg.type == "request"
        assert msg.payload["action"] == "run_task"
        assert msg.sender == "client-1"

    def test_message_to_dict(self):
        msg = RemoteMessage(
            type="response",
            payload={"result": "ok"},
            sender="server",
        )
        data = msg.to_dict()
        assert data["type"] == "response"
        assert data["payload"]["result"] == "ok"


class TestRemoteBridge:
    def test_bridge_creation(self):
        bridge = RemoteBridge(host="127.0.0.1", port=9000)
        assert bridge.host == "127.0.0.1"
        assert bridge.port == 9000
        assert bridge.running is False

    @pytest.mark.asyncio
    async def test_bridge_start_stop(self):
        bridge = RemoteBridge(port=0)

        await bridge.start()
        assert bridge.running is True

        await bridge.stop()
        assert bridge.running is False

    @pytest.mark.asyncio
    async def test_send_message(self):
        bridge = RemoteBridge(port=0)
        await bridge.start()

        msg = RemoteMessage(type="ping", payload={}, sender="test")
        await bridge.send(msg)

        await bridge.stop()

    @pytest.mark.asyncio
    async def test_on_message_handler(self):
        bridge = RemoteBridge(port=0)
        received = []

        async def handler(msg: RemoteMessage) -> None:
            received.append(msg)

        bridge.on_message(handler)
        await bridge.start()

        await bridge._handle_incoming(
            {"type": "task", "payload": {"cmd": "ls"}, "sender": "remote"}
        )

        await bridge.stop()

        assert len(received) == 1
        assert received[0].type == "task"
        assert received[0].payload["cmd"] == "ls"

    @pytest.mark.asyncio
    async def test_handle_invalid_message(self):
        bridge = RemoteBridge(port=0)
        await bridge.start()

        # Should not raise
        await bridge._handle_incoming({"invalid": "data"})

        await bridge.stop()

    def test_set_handler(self):
        bridge = RemoteBridge(port=0)

        async def handler(msg: RemoteMessage) -> None:
            pass

        bridge.on_message(handler)
        assert len(bridge._handlers) == 1

    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        bridge = RemoteBridge(port=0)
        calls = []

        async def handler1(msg: RemoteMessage) -> None:
            calls.append("h1")

        async def handler2(msg: RemoteMessage) -> None:
            calls.append("h2")

        bridge.on_message(handler1)
        bridge.on_message(handler2)
        await bridge.start()

        await bridge._handle_incoming(
            {"type": "test", "payload": {}, "sender": "x"}
        )

        await bridge.stop()

        assert calls == ["h1", "h2"]
