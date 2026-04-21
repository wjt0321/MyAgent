"""Weixin (WeChat) platform adapter for MyAgent.

Connects to WeChat via iLink Bot API or webhook mode.
Supports personal WeChat accounts.
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

ILINK_BASE_URL = "https://ilinkai.weixin.qq.com"


class WeixinAdapter(BasePlatformAdapter):
    """Weixin (WeChat) platform adapter."""

    name = "Weixin"

    def __init__(self, config: PlatformConfig) -> None:
        super().__init__(config, Platform.WEIXIN)
        self.token = config.token or ""
        self.account_id = config.extra.get("account_id", "")
        self.base_url = config.extra.get("base_url", ILINK_BASE_URL).rstrip("/")
        self._dedup = MessageDeduplicator()
        self._session: Any = None
        self._context_tokens: Dict[str, str] = {}

    async def connect(self) -> bool:
        if not AIOHTTP_AVAILABLE:
            logger.error("[%s] aiohttp not installed. Run: pip install aiohttp", self.name)
            return False
        if not self.token:
            logger.error("[%s] WEIXIN_TOKEN required", self.name)
            return False

        self._session = aiohttp.ClientSession()
        self._running = True
        logger.info("[%s] Connected (account=%s)", self.name, self.account_id or "default")
        return True

    async def disconnect(self) -> None:
        self._running = False
        if self._session:
            await self._session.close()
            self._session = None
        logger.info("[%s] Disconnected", self.name)

    async def _api_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make an API request to the Weixin iLink API."""
        url = f"{self.base_url}/ilink/bot/{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        try:
            async with self._session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                return data
        except Exception as e:
            logger.error("[%s] API request failed: %s", self.name, e)
            return {"errcode": -1, "errmsg": str(e)}

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": content[:4000],
            "context_token": self._context_tokens.get(chat_id, ""),
        }

        data = await self._api_request("sendmessage", payload)
        if data.get("errcode") == 0:
            # Update context token
            if "context_token" in data:
                self._context_tokens[chat_id] = data["context_token"]
            return SendResult(success=True, message_id=data.get("msg_id"), raw_response=data)

        return SendResult(
            success=False,
            error=data.get("errmsg", "Unknown error"),
            retryable=data.get("errcode") in (-1, 1001, 1002),
        )

    async def poll_updates(self) -> None:
        """Long-poll for updates. Run this in a background task."""
        offset = 0
        while self._running:
            payload = {
                "offset": offset,
                "limit": 100,
                "timeout": 35,
            }
            data = await self._api_request("getupdates", payload)

            if data.get("errcode") != 0:
                logger.warning("[%s] getupdates error: %s", self.name, data.get("errmsg"))
                await asyncio.sleep(5)
                continue

            updates = data.get("updates", [])
            for update in updates:
                offset = max(offset, update.get("update_id", 0) + 1)
                await self._process_update(update)

            if not updates:
                await asyncio.sleep(1)

    async def _process_update(self, update: Dict[str, Any]) -> None:
        """Process a single update."""
        msg = update.get("message", {})
        msg_id = str(msg.get("msg_id", ""))

        if self._dedup.is_duplicate(msg_id):
            return

        chat = msg.get("chat", {})
        sender = msg.get("from", {})

        chat_id = str(chat.get("id", ""))
        user_id = str(sender.get("id", ""))
        chat_type = "group" if chat.get("type") == "group" else "dm"

        source = self.build_source(
            chat_id=chat_id,
            user_id=user_id,
            chat_type=chat_type,
            user_name=sender.get("nickname"),
        )

        text = msg.get("text", "")
        msg_type = msg.get("type", "text")

        mapped_type = MessageType.TEXT
        if msg_type == "image":
            mapped_type = MessageType.IMAGE
        elif msg_type == "voice":
            mapped_type = MessageType.VOICE
        elif msg_type == "file":
            mapped_type = MessageType.FILE

        event = MessageEvent(
            text=text,
            message_type=mapped_type,
            source=source,
            raw_message=update,
            message_id=msg_id,
            platform_update_id=update.get("update_id"),
        )

        await self.handle_message(event)

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        return {"name": "WeChat Chat", "type": "dm"}
