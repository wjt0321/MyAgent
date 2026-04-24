"""Telegram platform adapter for MyAgent.

Uses HTTP long-polling or webhook for message handling.
"""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
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

TELEGRAM_API_BASE = "https://api.telegram.org/bot"


class TelegramAdapter(BasePlatformAdapter):
    """Telegram Bot platform adapter."""

    name = "Telegram"

    def __init__(self, config: PlatformConfig) -> None:
        super().__init__(config, Platform.TELEGRAM)
        self.token = config.token or ""
        self._session: Any = None
        self._offset = 0
        self._dedup = MessageDeduplicator()
        # Track pending permission requests: callback_id -> (future, tool_name)
        self._pending_permissions: Dict[str, asyncio.Future[bool]] = {}

    @property
    def api_base(self) -> str:
        return f"{TELEGRAM_API_BASE}{self.token}"

    async def connect(self) -> bool:
        if not AIOHTTP_AVAILABLE:
            logger.error("[%s] aiohttp not installed. Run: pip install aiohttp", self.name)
            return False
        if not self.token:
            logger.error("[%s] TELEGRAM_BOT_TOKEN required", self.name)
            return False

        self._session = aiohttp.ClientSession()

        # Verify bot
        me = await self._api_request("GET", "/getMe")
        if not me.get("ok"):
            logger.error("[%s] getMe failed: %s", self.name, me.get("description"))
            return False

        bot_name = me["result"].get("username", "Unknown")
        logger.info("[%s] Connected as @%s", self.name, bot_name)

        self._running = True
        asyncio.create_task(self._poll_loop())
        return True

    async def disconnect(self) -> None:
        self._running = False
        # Cancel all pending permission futures
        for future in self._pending_permissions.values():
            if not future.done():
                future.cancel()
        self._pending_permissions.clear()
        if self._session:
            await self._session.close()
        logger.info("[%s] Disconnected", self.name)

    async def _api_request(
        self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a Telegram API request."""
        url = f"{self.api_base}{endpoint}"
        try:
            if method == "GET":
                async with self._session.get(url, params=payload) as resp:
                    return await resp.json()
            else:
                async with self._session.post(url, json=payload) as resp:
                    return await resp.json()
        except Exception as e:
            logger.error("[%s] API request failed: %s", self.name, e)
            return {"ok": False, "description": str(e)}

    async def _poll_loop(self) -> None:
        """Long-polling loop for updates."""
        while self._running:
            try:
                payload = {
                    "offset": self._offset,
                    "limit": 100,
                    "timeout": 30,
                }
                data = await self._api_request("GET", "/getUpdates", payload)

                if not data.get("ok"):
                    await asyncio.sleep(5)
                    continue

                updates = data.get("result", [])
                for update in updates:
                    self._offset = max(self._offset, update.get("update_id", 0) + 1)
                    await self._process_update(update)

                if not updates:
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error("[%s] Poll error: %s", self.name, e)
                await asyncio.sleep(5)

    async def _process_update(self, update: Dict[str, Any]) -> None:
        """Process a single update."""
        # Handle callback queries (inline keyboard button presses)
        callback_query = update.get("callback_query")
        if callback_query:
            await self._process_callback_query(callback_query)
            return

        msg = update.get("message") or update.get("edited_message")
        if not msg:
            return

        msg_id = str(msg.get("message_id", ""))
        if self._dedup.is_duplicate(msg_id):
            return

        chat = msg.get("chat", {})
        from_user = msg.get("from", {})

        chat_id = str(chat.get("id", ""))
        user_id = str(from_user.get("id", ""))
        chat_type = "group" if chat.get("type") in ("group", "supergroup") else "dm"

        source = self.build_source(
            chat_id=chat_id,
            user_id=user_id,
            user_name=from_user.get("username") or from_user.get("first_name"),
            chat_type=chat_type,
        )

        # Handle different message types
        text = ""
        msg_type = MessageType.TEXT

        if "text" in msg:
            text = msg["text"]
        elif "photo" in msg:
            text = msg.get("caption", "")
            msg_type = MessageType.PHOTO
        elif "voice" in msg:
            text = "[Voice message]"
            msg_type = MessageType.VOICE
        elif "document" in msg:
            text = msg.get("caption", "[Document]")
            msg_type = MessageType.DOCUMENT

        event = MessageEvent(
            text=text,
            message_type=msg_type,
            source=source,
            raw_message=update,
            message_id=msg_id,
            platform_update_id=update.get("update_id"),
        )

        await self.handle_message(event)

    async def _process_callback_query(self, callback_query: Dict[str, Any]) -> None:
        """Process an inline keyboard callback query."""
        callback_id = callback_query.get("id", "")
        data = callback_query.get("data", "")

        # Answer the callback query to remove loading state
        await self._api_request("POST", "/answerCallbackQuery", {
            "callback_query_id": callback_id,
        })

        # Check if this is a permission response
        if callback_id in self._pending_permissions:
            future = self._pending_permissions.pop(callback_id)
            if data == "approve":
                if not future.done():
                    future.set_result(True)
            elif data == "deny":
                if not future.done():
                    future.set_result(False)
            logger.debug("[%s] Permission callback resolved: %s", self.name, data)

    async def send_permission_request(
        self,
        chat_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        reason: str,
        timeout: float = 300.0,
    ) -> bool:
        """Send a permission request with inline keyboard and wait for response.

        Returns True if approved, False if denied or timed out.
        """
        args_text = json.dumps(arguments, ensure_ascii=False, indent=2)[:500]
        text = (
            f"🔐 **Permission Request**\n\n"
            f"Tool: `{tool_name}`\n"
            f"Reason: {reason}\n\n"
            f"Arguments:\n```json\n{args_text}\n```"
        )

        callback_id = secrets.token_urlsafe(16)
        future: asyncio.Future[bool] = asyncio.get_event_loop().create_future()
        self._pending_permissions[callback_id] = future

        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Allow", "callback_data": "approve"},
                    {"text": "❌ Deny", "callback_data": "deny"},
                ]
            ]
        }

        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text[:4096],
            "parse_mode": "Markdown",
            "reply_markup": keyboard,
        }

        data = await self._api_request("POST", "/sendMessage", payload)
        if not data.get("ok"):
            self._pending_permissions.pop(callback_id, None)
            logger.error("[%s] Failed to send permission request: %s", self.name, data.get("description"))
            return False

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            # Edit the message to show the decision
            decision_text = "✅ **Approved**" if result else "❌ **Denied**"
            sent_msg = data.get("result", {})
            await self._api_request("POST", "/editMessageText", {
                "chat_id": chat_id,
                "message_id": sent_msg.get("message_id"),
                "text": f"{text}\n\n{decision_text}",
                "parse_mode": "Markdown",
            })
            return result
        except asyncio.TimeoutError:
            self._pending_permissions.pop(callback_id, None)
            # Edit message to show timeout
            sent_msg = data.get("result", {})
            await self._api_request("POST", "/editMessageText", {
                "chat_id": chat_id,
                "message_id": sent_msg.get("message_id"),
                "text": f"{text}\n\n⏱️ **Timed out** (no response within {int(timeout)}s)",
                "parse_mode": "Markdown",
            })
            logger.warning("[%s] Permission request timed out for %s", self.name, tool_name)
            return False
        except asyncio.CancelledError:
            self._pending_permissions.pop(callback_id, None)
            raise

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": content[:4096],
            "parse_mode": "Markdown",
        }
        if reply_to:
            payload["reply_parameters"] = {"message_id": int(reply_to)}

        data = await self._api_request("POST", "/sendMessage", payload)
        if data.get("ok"):
            result = data.get("result", {})
            return SendResult(
                success=True,
                message_id=str(result.get("message_id")),
                raw_response=data,
            )

        return SendResult(
            success=False,
            error=data.get("description", "Unknown error"),
            retryable=data.get("error_code") in (429, 500, 502, 503, 504),
        )

    async def send_typing(self, chat_id: str, metadata: Any = None) -> None:
        await self._api_request("POST", "/sendChatAction", {
            "chat_id": chat_id,
            "action": "typing",
        })

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        data = await self._api_request("GET", "/getChat", {"chat_id": chat_id})
        if data.get("ok"):
            result = data.get("result", {})
            return {
                "name": result.get("title") or result.get("username", "Unknown"),
                "type": "group" if result.get("type") in ("group", "supergroup") else "dm",
            }
        return {"name": "Unknown", "type": "dm"}
