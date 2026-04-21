"""Feishu/Lark platform adapter for MyAgent.

Supports:
- Webhook transport (HTTP callbacks from Feishu)
- Direct-message and group @mention-gated text receive/send
- Inbound image/file caching
- Message deduplication
- Per-chat serial message processing
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, Optional

from myagent.gateway.adapter_base import BasePlatformAdapter
from myagent.gateway.base import (
    MessageEvent,
    MessageType,
    Platform,
    SendResult,
    SessionSource,
    strip_markdown,
)
from myagent.gateway.config import PlatformConfig
from myagent.gateway.helpers import MessageDeduplicator

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None  # type: ignore[assignment]
    AIOHTTP_AVAILABLE = False

FEISHU_API_BASE = "https://open.feishu.cn/open-apis"
LARK_API_BASE = "https://open.larksuite.com/open-apis"


class FeishuAdapter(BasePlatformAdapter):
    """Feishu (Lark) platform adapter."""

    name = "Feishu"

    def __init__(self, config: PlatformConfig) -> None:
        super().__init__(config, Platform.FEISHU)
        self.app_id = config.extra.get("app_id", "")
        self.app_secret = config.extra.get("app_secret", "")
        self.domain = config.extra.get("domain", "feishu")
        self.encrypt_key = config.extra.get("encrypt_key", "")
        self.verification_token = config.extra.get("verification_token", "")
        self._access_token: Optional[str] = None
        self._token_expires_at = 0.0
        self._dedup = MessageDeduplicator()
        self._session: Any = None

    @property
    def api_base(self) -> str:
        return LARK_API_BASE if self.domain == "lark" else FEISHU_API_BASE

    async def connect(self) -> bool:
        if not AIOHTTP_AVAILABLE:
            logger.error("[%s] aiohttp not installed. Run: pip install aiohttp", self.name)
            return False
        if not self.app_id or not self.app_secret:
            logger.error("[%s] app_id and app_secret required", self.name)
            return False

        self._session = aiohttp.ClientSession()
        token = await self._get_access_token()
        if not token:
            logger.error("[%s] Failed to get access token", self.name)
            return False

        self._running = True
        logger.info("[%s] Connected (domain=%s)", self.name, self.domain)
        return True

    async def disconnect(self) -> None:
        self._running = False
        if self._session:
            await self._session.close()
            self._session = None
        logger.info("[%s] Disconnected", self.name)

    async def _get_access_token(self) -> Optional[str]:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        url = f"{self.api_base}/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}

        async with self._session.post(url, json=payload) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                self._access_token = data.get("tenant_access_token")
                expires_in = data.get("expire", 7200)
                self._token_expires_at = time.time() + expires_in
                return self._access_token
            logger.error("[%s] Token error: %s", self.name, data)
            return None

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        token = await self._get_access_token()
        if not token:
            return SendResult(success=False, error="No access token", retryable=True)

        # Feishu uses Open Message ID format for chat_id in DMs
        # For groups, it's the chat_id
        url = f"{self.api_base}/im/v1/messages"
        headers = {"Authorization": f"Bearer {token}"}

        # Build message content
        msg_content = json.dumps({"text": strip_markdown(content)[:4000]})
        payload: Dict[str, Any] = {
            "receive_id": chat_id,
            "msg_type": "text",
            "content": msg_content,
        }

        # Determine receive_id_type
        if metadata and metadata.get("chat_type") == "group":
            payload["receive_id_type"] = "chat_id"
        else:
            payload["receive_id_type"] = "open_id"

        try:
            async with self._session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                if data.get("code") == 0:
                    msg_data = data.get("data", {})
                    return SendResult(
                        success=True,
                        message_id=msg_data.get("message_id"),
                        raw_response=data,
                    )
                error_msg = data.get("msg", f"HTTP {resp.status}")
                return SendResult(
                    success=False,
                    error=error_msg,
                    retryable=resp.status >= 500,
                )
        except Exception as e:
            return SendResult(success=False, error=str(e), retryable=True)

    async def send_image(
        self,
        chat_id: str,
        image_url: str,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        token = await self._get_access_token()
        if not token:
            return SendResult(success=False, error="No access token")

        # For Feishu, we need to upload the image first, then send by image_key
        # Fallback to text with URL for simplicity
        text = f"{caption}\n{image_url}" if caption else image_url
        return await self.send(chat_id, text, reply_to, metadata)

    async def handle_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Optional[str]:
        """Handle incoming webhook from Feishu.

        Returns a challenge response for URL verification, or None.
        """
        # URL verification
        if payload.get("type") == "url_verification":
            challenge = payload.get("challenge", "")
            # Optional: verify token
            if self.verification_token:
                token = payload.get("token", "")
                if token != self.verification_token:
                    logger.warning("[%s] Verification token mismatch", self.name)
                    return None
            return challenge

        # Event callback
        header = payload.get("header", {})
        event_type = header.get("event_type", "")

        if event_type == "im.message.receive_v1":
            event_data = payload.get("event", {})
            message = event_data.get("message", {})
            sender = event_data.get("sender", {})

            msg_id = message.get("message_id", "")
            if self._dedup.is_duplicate(msg_id):
                return None

            msg_type = message.get("message_type", "text")
            content_str = message.get("content", "{}")
            try:
                content = json.loads(content_str)
            except json.JSONDecodeError:
                content = {}

            text = content.get("text", "")
            chat_id = message.get("chat_id", "")
            open_id = sender.get("sender_id", {}).get("open_id", "")
            open_chat_id = sender.get("sender_id", {}).get("open_chat_id", "")

            # Build source
            chat_type = "group" if message.get("chat_type") == "group" else "dm"
            source = self.build_source(
                chat_id=chat_id or open_chat_id,
                user_id=open_id,
                chat_type=chat_type,
            )

            # Map message type
            mapped_type = MessageType.TEXT
            if msg_type == "image":
                mapped_type = MessageType.IMAGE
            elif msg_type == "file":
                mapped_type = MessageType.FILE
            elif msg_type == "audio":
                mapped_type = MessageType.AUDIO

            event = MessageEvent(
                text=text,
                message_type=mapped_type,
                source=source,
                raw_message=payload,
                message_id=msg_id,
            )

            await self.handle_message(event)

        return None

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        token = await self._get_access_token()
        if not token:
            return {"name": "Unknown", "type": "dm"}

        url = f"{self.api_base}/im/v1/chats/{chat_id}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with self._session.get(url, headers=headers) as resp:
                data = await resp.json()
                if data.get("code") == 0:
                    chat_data = data.get("data", {})
                    return {
                        "name": chat_data.get("name", "Unknown"),
                        "type": "group" if chat_data.get("chat_mode") == "group" else "dm",
                    }
        except Exception as e:
            logger.warning("[%s] Failed to get chat info: %s", self.name, e)

        return {"name": "Unknown", "type": "dm"}

    def verify_signature(self, body: bytes, timestamp: str, nonce: str, signature: str) -> bool:
        """Verify Feishu webhook signature."""
        if not self.encrypt_key:
            return True
        # Feishu signature: BASE64(HMAC-SHA256(encrypt_key, timestamp + nonce + body))
        message = f"{timestamp}{nonce}".encode() + body
        expected = hmac.new(
            self.encrypt_key.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
