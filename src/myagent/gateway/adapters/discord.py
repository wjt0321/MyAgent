"""Discord platform adapter for MyAgent.

Uses Discord Gateway WebSocket for real-time messaging.
Supports:
- Gateway WebSocket connection with heartbeat
- Message receive/send
- DM and guild channel support
- Message deduplication
- Auto-reconnect on disconnect
"""

from __future__ import annotations

import asyncio
import json
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
DISCORD_GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"


class DiscordAdapter(BasePlatformAdapter):
    """Discord platform adapter using Gateway WebSocket."""

    name = "Discord"

    def __init__(self, config: PlatformConfig) -> None:
        super().__init__(config, Platform.DISCORD)
        self.token = config.token or ""
        self._session: Any = None
        self._ws: Any = None
        self._heartbeat_interval = 0
        self._heartbeat_task: Any = None
        self._sequence: Optional[int] = None
        self._session_id: Optional[str] = None
        self._resume_gateway_url: Optional[str] = None
        self._dedup = MessageDeduplicator()
        self._bot_id: Optional[str] = None
        self._reconnect_delay = 5.0

    async def connect(self) -> bool:
        if not AIOHTTP_AVAILABLE:
            logger.error("[%s] aiohttp not installed. Run: pip install aiohttp", self.name)
            return False
        if not self.token:
            logger.error("[%s] DISCORD_BOT_TOKEN required", self.name)
            return False

        self._session = aiohttp.ClientSession()

        # Get bot info
        me = await self._api_request("GET", "/users/@me")
        if me is None:
            logger.error("[%s] Failed to authenticate", self.name)
            return False

        self._bot_id = me.get("id")
        bot_name = me.get("username", "Unknown")
        logger.info("[%s] Authenticated as %s", self.name, bot_name)

        # Connect to Gateway
        return await self._connect_gateway()

    async def _connect_gateway(self) -> bool:
        """Connect to Discord Gateway WebSocket."""
        gateway_url = self._resume_gateway_url or DISCORD_GATEWAY_URL

        try:
            self._ws = await self._session.ws_connect(gateway_url)
            self._running = True
            asyncio.create_task(self._ws_loop())
            return True
        except Exception as e:
            logger.error("[%s] Gateway connection failed: %s", self.name, e)
            return False

    async def disconnect(self) -> None:
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
        logger.info("[%s] Disconnected", self.name)

    async def _api_request(
        self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make a Discord API request."""
        url = f"{DISCORD_API_BASE}{endpoint}"
        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
        }

        try:
            if method == "GET":
                async with self._session.get(url, headers=headers, params=payload) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    logger.error("[%s] API %s %s failed: HTTP %d", self.name, method, endpoint, resp.status)
                    return None
            else:
                async with self._session.post(url, headers=headers, json=payload) as resp:
                    if resp.status in (200, 201):
                        return await resp.json()
                    logger.error("[%s] API %s %s failed: HTTP %d", self.name, method, endpoint, resp.status)
                    return None
        except Exception as e:
            logger.error("[%s] API request failed: %s", self.name, e)
            return None

    async def _ws_loop(self) -> None:
        """Main WebSocket receive loop with auto-reconnect."""
        while self._running:
            try:
                msg = await self._ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.json()
                    await self._handle_gateway_message(data)
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    logger.warning("[%s] WebSocket closed, reconnecting in %.0fs...", self.name, self._reconnect_delay)
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, 300)  # Max 5 minutes
                    await self._reconnect()
                    break
            except Exception as e:
                logger.error("[%s] WebSocket error: %s", self.name, e)
                await asyncio.sleep(self._reconnect_delay)
                await self._reconnect()
                break

    async def _reconnect(self) -> None:
        """Reconnect to Gateway, attempting resume if possible."""
        if self._ws:
            await self._ws.close()

        if self._session_id and self._sequence:
            # Try to resume
            gateway_url = self._resume_gateway_url or DISCORD_GATEWAY_URL
            try:
                self._ws = await self._session.ws_connect(gateway_url)
                await self._ws.send_json({
                    "op": 6,  # Resume
                    "d": {
                        "token": self.token,
                        "session_id": self._session_id,
                        "seq": self._sequence,
                    }
                })
                self._running = True
                asyncio.create_task(self._ws_loop())
                logger.info("[%s] Resuming session %s", self.name, self._session_id)
                return
            except Exception as e:
                logger.warning("[%s] Resume failed: %s", self.name, e)
                self._session_id = None
                self._sequence = None

        # Fresh connection
        await self._connect_gateway()

    async def _handle_gateway_message(self, data: Dict[str, Any]) -> None:
        """Handle a Discord Gateway message."""
        op = data.get("op")
        d = data.get("d", {})
        t = data.get("t")
        s = data.get("s")

        if s is not None:
            self._sequence = s

        if op == 10:  # Hello
            self._heartbeat_interval = d.get("heartbeat_interval", 45000) / 1000
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            await self._identify()

        elif op == 11:  # Heartbeat ACK
            pass

        elif op == 0:  # Dispatch
            await self._handle_dispatch(t, d)

        elif op == 7:  # Reconnect
            logger.info("[%s] Gateway requested reconnect", self.name)
            await self._reconnect()

        elif op == 9:  # Invalid Session
            logger.warning("[%s] Invalid session, reconnecting", self.name)
            self._session_id = None
            self._sequence = None
            await asyncio.sleep(5)
            await self._reconnect()

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats."""
        try:
            while self._running:
                await asyncio.sleep(self._heartbeat_interval)
                if self._ws and not self._ws.closed:
                    await self._ws.send_json({
                        "op": 1,
                        "d": self._sequence,
                    })
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("[%s] Heartbeat error: %s", self.name, e)

    async def _identify(self) -> None:
        """Send identify payload."""
        await self._ws.send_json({
            "op": 2,
            "d": {
                "token": self.token,
                "intents": 513,  # GUILDS + GUILD_MESSAGES
                "properties": {
                    "os": "linux",
                    "browser": "MyAgent",
                    "device": "MyAgent",
                },
            }
        })

    async def _handle_dispatch(self, event_type: Optional[str], data: Dict[str, Any]) -> None:
        """Handle Discord dispatch events."""
        if event_type == "READY":
            self._session_id = data.get("session_id")
            self._resume_gateway_url = data.get("resume_gateway_url")
            self._reconnect_delay = 5.0  # Reset backoff
            logger.info("[%s] Gateway ready, session_id=%s", self.name, self._session_id)

        elif event_type == "MESSAGE_CREATE":
            await self._process_message(data)

    async def _process_message(self, data: Dict[str, Any]) -> None:
        """Process a Discord message."""
        msg_id = data.get("id", "")
        if self._dedup.is_duplicate(msg_id):
            return

        author = data.get("author", {})
        user_id = author.get("id", "")

        # Ignore bot's own messages
        if user_id == self._bot_id:
            return

        # Ignore other bots
        if author.get("bot", False):
            return

        channel_id = data.get("channel_id", "")
        content = data.get("content", "")
        guild_id = data.get("guild_id")

        # Remove @bot mention
        if self._bot_id:
            content = content.replace(f"<@{self._bot_id}>", "").replace(f"<@!{self._bot_id}>", "").strip()

        # Determine chat type
        channel_type = data.get("channel_type", 0)
        chat_type = "dm" if channel_type == 1 else "group"

        source = self.build_source(
            chat_id=channel_id,
            user_id=user_id,
            user_name=author.get("username"),
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
        payload: Dict[str, Any] = {
            "content": content[:2000],  # Discord limit
        }
        if reply_to:
            payload["message_reference"] = {"message_id": reply_to}

        data = await self._api_request("POST", f"/channels/{chat_id}/messages", payload)
        if data:
            return SendResult(
                success=True,
                message_id=data.get("id"),
                raw_response=data,
            )

        return SendResult(
            success=False,
            error="Failed to send message",
            retryable=True,
        )

    async def send_typing(self, chat_id: str, metadata: Any = None) -> None:
        await self._api_request("POST", f"/channels/{chat_id}/typing")

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        data = await self._api_request("GET", f"/channels/{chat_id}")
        if data:
            return {
                "name": data.get("name", "Unknown"),
                "type": "dm" if data.get("type") == 1 else "group",
            }
        return {"name": "Unknown", "type": "dm"}
