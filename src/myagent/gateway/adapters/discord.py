"""Discord platform adapter for MyAgent.

Uses discord.py or aiohttp for WebSocket-based message handling.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from myagent.gateway.adapter_base import BasePlatformAdapter
from myagent.gateway.base import (
    MessageEvent,
    MessageType,
    Platform,
    SendResult,
)
from myagent.gateway.config import PlatformConfig
from myagent.gateway.helpers import MessageDeduplicator

logger = logging.getLogger(__name__)

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None  # type: ignore[assignment]
    AIOHTTP_AVAILABLE = False

DISCORD_API_BASE = "https://discord.com/api/v10"


class DiscordAdapter(BasePlatformAdapter):
    """Discord platform adapter using HTTP + Gateway WebSocket."""

    name = "Discord"

    def __init__(self, config: PlatformConfig) -> None:
        super().__init__(config, Platform.DISCORD)
        self.token = config.token or ""
        self._session: Any = None
        self._ws: Any = None
        self._heartbeat_task: Any = None
        self._sequence: Optional[int] = None
        self._session_id: Optional[str] = None
        self._dedup = MessageDeduplicator()
        self._gateway_url: Optional[str] = None

    async def connect(self) -> bool:
        if not AIOHTTP_AVAILABLE:
            logger.error("[%s] aiohttp not installed. Run: pip install aiohttp", self.name)
            return False
        if not self.token:
            logger.error("[%s] DISCORD_BOT_TOKEN required", self.name)
            return False

        self._session = aiohttp.ClientSession()

        # Get gateway URL
        async with self._session.get(
            f"{DISCORD_API_BASE}/gateway/bot",
            headers={"Authorization": f"Bot {self.token}"},
        ) as resp:
            data = await resp.json()
            self._gateway_url = data.get("url", "wss://gateway.discord.gg")

        # Connect to WebSocket
        self._ws = await self._session.ws_connect(
            f"{self._gateway_url}?v=10&encoding=json"
        )

        self._running = True
        asyncio.create_task(self._ws_loop())
        logger.info("[%s] Connected", self.name)
        return True

    async def disconnect(self) -> None:
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
        logger.info("[%s] Disconnected", self.name)

    async def _ws_loop(self) -> None:
        """Main WebSocket receive loop."""
        while self._running:
            try:
                msg = await self._ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.json()
                    await self._handle_ws_message(data)
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break
            except Exception as e:
                logger.error("[%s] WebSocket error: %s", self.name, e)
                await asyncio.sleep(5)

    async def _handle_ws_message(self, data: Dict[str, Any]) -> None:
        """Handle a Discord Gateway message."""
        op = data.get("op", 0)

        if op == 10:  # Hello
            interval = data["d"]["heartbeat_interval"] / 1000
            self._heartbeat_task = asyncio.create_task(self._heartbeat(interval))
            await self._identify()

        elif op == 11:  # Heartbeat ACK
            pass

        elif op == 0:  # Dispatch
            self._sequence = data.get("s")
            event_type = data.get("t", "")

            if event_type == "READY":
                self._session_id = data["d"]["session_id"]

            elif event_type == "MESSAGE_CREATE":
                await self._process_message(data["d"])

    async def _heartbeat(self, interval: float) -> None:
        """Send periodic heartbeats."""
        while self._running:
            await asyncio.sleep(interval)
            if self._ws and not self._ws.closed:
                await self._ws.send_json({"op": 1, "d": self._sequence})

    async def _identify(self) -> None:
        """Send identify payload."""
        await self._ws.send_json({
            "op": 2,
            "d": {
                "token": f"Bot {self.token}",
                "intents": 512 + 1024,  # GUILD_MESSAGES + GUILD_MESSAGE_CONTENT
                "properties": {
                    "os": "linux",
                    "browser": "myagent",
                    "device": "myagent",
                },
            },
        })

    async def _process_message(self, data: Dict[str, Any]) -> None:
        """Process a Discord message."""
        msg_id = data.get("id", "")
        if self._dedup.is_duplicate(msg_id):
            return

        author = data.get("author", {})
        # Ignore bot messages (including self)
        if author.get("bot", False):
            return

        user_id = str(author.get("id", ""))
        user_name = author.get("username", "")
        channel_id = str(data.get("channel_id", ""))
        guild_id = data.get("guild_id")

        content = data.get("content", "")

        # Check for @mention
        bot_id = None
        mentions = data.get("mentions", [])
        for mention in mentions:
            if mention.get("bot", False):
                bot_id = mention.get("id")
                break

        # Remove @mention from content
        if bot_id:
            content = content.replace(f"<@{bot_id}>", "").replace(f"<@!{bot_id}>", "").strip()

        chat_type = "group" if guild_id else "dm"

        source = self.build_source(
            chat_id=channel_id,
            user_id=user_id,
            user_name=user_name,
            chat_type=chat_type,
        )

        event = MessageEvent(
            text=content,
            message_type=MessageType.TEXT,
            source=source,
            raw_message=data,
            message_id=msg_id,
        )

        await self.handle_message(event)

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        url = f"{DISCORD_API_BASE}/channels/{chat_id}/messages"
        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {"content": content[:2000]}
        if reply_to:
            payload["message_reference"] = {"message_id": reply_to}

        try:
            async with self._session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                if resp.status == 200:
                    return SendResult(success=True, message_id=data.get("id"), raw_response=data)
                return SendResult(
                    success=False,
                    error=data.get("message", f"HTTP {resp.status}"),
                    retryable=resp.status >= 500,
                )
        except Exception as e:
            return SendResult(success=False, error=str(e), retryable=True)

    async def send_typing(self, chat_id: str, metadata: Any = None) -> None:
        url = f"{DISCORD_API_BASE}/channels/{chat_id}/typing"
        headers = {"Authorization": f"Bot {self.token}"}
        try:
            async with self._session.post(url, headers=headers) as resp:
                pass
        except Exception as e:
            logger.debug("[%s] send_typing failed: %s", self.name, e)

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        url = f"{DISCORD_API_BASE}/channels/{chat_id}"
        headers = {"Authorization": f"Bot {self.token}"}
        try:
            async with self._session.get(url, headers=headers) as resp:
                data = await resp.json()
                if resp.status == 200:
                    return {
                        "name": data.get("name", "Unknown"),
                        "type": "group" if data.get("type") == 0 else "dm",
                    }
        except Exception as e:
            logger.warning("[%s] Failed to get chat info: %s", self.name, e)
        return {"name": "Unknown", "type": "dm"}
