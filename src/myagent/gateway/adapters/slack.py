"""Slack platform adapter for MyAgent.

Uses Slack Bolt or direct WebSocket for real-time messaging.
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

SLACK_API_BASE = "https://slack.com/api"


class SlackAdapter(BasePlatformAdapter):
    """Slack platform adapter using Socket Mode."""

    name = "Slack"

    def __init__(self, config: PlatformConfig) -> None:
        super().__init__(config, Platform.SLACK)
        self.token = config.token or ""
        self._session: Any = None
        self._ws: Any = None
        self._dedup = MessageDeduplicator()
        self._bot_id: Optional[str] = None

    async def connect(self) -> bool:
        if not AIOHTTP_AVAILABLE:
            logger.error("[%s] aiohttp not installed. Run: pip install aiohttp", self.name)
            return False
        if not self.token:
            logger.error("[%s] SLACK_BOT_TOKEN required", self.name)
            return False

        self._session = aiohttp.ClientSession()

        # Get bot info
        bot_info = await self._api_request("GET", "/auth.test")
        if not bot_info.get("ok"):
            logger.error("[%s] Auth failed: %s", self.name, bot_info.get("error"))
            return False

        self._bot_id = bot_info.get("user_id")
        logger.info("[%s] Connected as %s", self.name, bot_info.get("user"))

        # Open Socket Mode connection
        apps_connect = await self._api_request("POST", "/apps.connections.open")
        if not apps_connect.get("ok"):
            logger.error("[%s] Socket mode open failed: %s", self.name, apps_connect.get("error"))
            return False

        ws_url = apps_connect.get("url")
        self._ws = await self._session.ws_connect(ws_url)

        self._running = True
        asyncio.create_task(self._ws_loop())
        return True

    async def disconnect(self) -> None:
        self._running = False
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
        logger.info("[%s] Disconnected", self.name)

    async def _api_request(
        self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a Slack API request."""
        url = f"{SLACK_API_BASE}{endpoint}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            if method == "GET":
                async with self._session.get(url, headers=headers, params=payload) as resp:
                    return await resp.json()
            else:
                async with self._session.post(url, headers=headers, json=payload) as resp:
                    return await resp.json()
        except Exception as e:
            logger.error("[%s] API request failed: %s", self.name, e)
            return {"ok": False, "error": str(e)}

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
        """Handle a Slack Socket Mode message."""
        envelope_id = data.get("envelope_id")

        # Acknowledge
        if envelope_id:
            await self._ws.send_json({"envelope_id": envelope_id})

        payload = data.get("payload", {})
        event = payload.get("event", {})
        event_type = event.get("type", "")

        if event_type == "message" and not event.get("subtype"):
            await self._process_message(event)

    async def _process_message(self, data: Dict[str, Any]) -> None:
        """Process a Slack message."""
        msg_id = data.get("client_msg_id") or data.get("ts", "")
        if self._dedup.is_duplicate(msg_id):
            return

        user_id = data.get("user", "")
        # Ignore bot's own messages
        if user_id == self._bot_id:
            return

        channel_id = data.get("channel", "")
        text = data.get("text", "")

        # Remove @bot mention
        if self._bot_id:
            text = text.replace(f"<@{self._bot_id}>", "").strip()

        thread_ts = data.get("thread_ts")

        # Determine chat type
        channel_type = data.get("channel_type", "channel")
        chat_type = "dm" if channel_type == "im" else "group"

        source = self.build_source(
            chat_id=channel_id,
            user_id=user_id,
            chat_type=chat_type,
            thread_id=thread_ts,
        )

        event = MessageEvent(
            text=text,
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
            "channel": chat_id,
            "text": content[:4000],
        }
        if reply_to:
            payload["thread_ts"] = reply_to

        data = await self._api_request("POST", "/chat.postMessage", payload)
        if data.get("ok"):
            msg_data = data.get("message", {})
            return SendResult(
                success=True,
                message_id=msg_data.get("ts"),
                raw_response=data,
            )

        return SendResult(
            success=False,
            error=data.get("error", "Unknown error"),
            retryable=data.get("error") in ("ratelimited", "fatal_error"),
        )

    async def send_typing(self, chat_id: str, metadata: Any = None) -> None:
        # Slack uses assistant.threads.setStatus for typing
        pass

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        data = await self._api_request("GET", "/conversations.info", {"channel": chat_id})
        if data.get("ok"):
            channel = data.get("channel", {})
            return {
                "name": channel.get("name", "Unknown"),
                "type": "group" if channel.get("is_channel") else "dm",
            }
        return {"name": "Unknown", "type": "dm"}
