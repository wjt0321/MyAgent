"""QQ platform adapter for MyAgent.

Uses QQ Bot Official API v2.
Supports group and direct message interactions.
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

QQ_API_BASE = "https://api.sgroup.qq.com"
QQ_SANDBOX_BASE = "https://sandbox.api.sgroup.qq.com"


class QQAdapter(BasePlatformAdapter):
    """QQ Bot platform adapter."""

    name = "QQ"

    def __init__(self, config: PlatformConfig) -> None:
        super().__init__(config, Platform.QQ)
        self.app_id = config.extra.get("app_id", "")
        self.client_secret = config.extra.get("client_secret", "")
        self.sandbox = config.extra.get("sandbox", False)
        self._access_token: Optional[str] = None
        self._token_expires_at = 0.0
        self._dedup = MessageDeduplicator()
        self._session: Any = None
        self._allowed_users: set = set()
        self._group_allowed_users: set = set()

        # Parse allowlists
        allow_from = config.extra.get("allow_from", "")
        if allow_from:
            self._allowed_users = set(u.strip() for u in allow_from.split(",") if u.strip())
        group_allow = config.extra.get("group_allow_from", "")
        if group_allow:
            self._group_allowed_users = set(u.strip() for u in group_allow.split(",") if u.strip())

    @property
    def api_base(self) -> str:
        return QQ_SANDBOX_BASE if self.sandbox else QQ_API_BASE

    async def connect(self) -> bool:
        if not AIOHTTP_AVAILABLE:
            logger.error("[%s] aiohttp not installed. Run: pip install aiohttp", self.name)
            return False
        if not self.app_id or not self.client_secret:
            logger.error("[%s] QQ_APP_ID and QQ_CLIENT_SECRET required", self.name)
            return False

        self._session = aiohttp.ClientSession()
        token = await self._get_access_token()
        if not token:
            logger.error("[%s] Failed to get access token", self.name)
            return False

        self._running = True
        logger.info("[%s] Connected (sandbox=%s)", self.name, self.sandbox)
        return True

    async def disconnect(self) -> None:
        self._running = False
        if self._session:
            await self._session.close()
            self._session = None
        logger.info("[%s] Disconnected", self.name)

    async def _get_access_token(self) -> Optional[str]:
        if self._access_token and asyncio.get_event_loop().time() < self._token_expires_at - 60:
            return self._access_token

        url = "https://bots.qq.com/app/getAppAccessToken"
        payload = {"appId": self.app_id, "clientSecret": self.client_secret}

        try:
            async with self._session.post(url, json=payload) as resp:
                data = await resp.json()
                if data.get("access_token"):
                    self._access_token = data["access_token"]
                    expires_in = data.get("expires_in", 7200)
                    self._token_expires_at = asyncio.get_event_loop().time() + expires_in
                    return self._access_token
                logger.error("[%s] Token error: %s", self.name, data)
        except Exception as e:
            logger.error("[%s] Token request failed: %s", self.name, e)
        return None

    async def _api_request(
        self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated API request."""
        token = await self._get_access_token()
        if not token:
            return {"code": -1, "message": "No access token"}

        url = f"{self.api_base}{endpoint}"
        headers = {
            "Authorization": f"QQBot {token}",
            "Content-Type": "application/json",
        }

        try:
            async with self._session.request(method, url, headers=headers, json=payload) as resp:
                data = await resp.json()
                return data
        except Exception as e:
            logger.error("[%s] API request failed: %s", self.name, e)
            return {"code": -1, "message": str(e)}

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        # Determine if this is a group or DM
        chat_type = metadata.get("chat_type", "dm") if metadata else "dm"

        if chat_type == "group":
            endpoint = f"/v2/groups/{chat_id}/messages"
        else:
            endpoint = f"/v2/users/{chat_id}/messages"

        payload: Dict[str, Any] = {
            "content": content[:4000],
            "msg_type": 0,  # Text message
        }
        if reply_to:
            payload["msg_id"] = reply_to

        data = await self._api_request("POST", endpoint, payload)
        if data.get("id"):
            return SendResult(success=True, message_id=data.get("id"), raw_response=data)

        return SendResult(
            success=False,
            error=data.get("message", "Unknown error"),
            retryable=data.get("code") in (10001, 10002, 10003),
        )

    async def send_image(
        self,
        chat_id: str,
        image_url: str,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        chat_type = metadata.get("chat_type", "dm") if metadata else "dm"

        if chat_type == "group":
            endpoint = f"/v2/groups/{chat_id}/messages"
        else:
            endpoint = f"/v2/users/{chat_id}/messages"

        payload: Dict[str, Any] = {
            "image": image_url,
            "msg_type": 1,  # Image message
        }
        if reply_to:
            payload["msg_id"] = reply_to

        data = await self._api_request("POST", endpoint, payload)
        if data.get("id"):
            return SendResult(success=True, message_id=data.get("id"))

        return SendResult(success=False, error=data.get("message", "Unknown error"))

    async def handle_webhook(self, payload: Dict[str, Any]) -> None:
        """Handle incoming webhook from QQ."""
        # Validate signature if needed
        op = payload.get("op", 0)

        # Heartbeat / Hello
        if op == 10 or op == 11:
            return

        # Dispatch
        if op == 0:
            event_type = payload.get("t", "")
            event_data = payload.get("d", {})

            if event_type in ("C2C_MESSAGE_CREATE", "GROUP_AT_MESSAGE_CREATE"):
                await self._process_message_event(event_data)

    async def _process_message_event(self, data: Dict[str, Any]) -> None:
        """Process a message event from QQ."""
        msg_id = data.get("id", "")
        if self._dedup.is_duplicate(msg_id):
            return

        author = data.get("author", {})
        user_id = str(author.get("id", ""))
        user_name = author.get("username", "")

        # Check allowlist
        chat_type = "group" if "group_id" in data else "dm"
        if chat_type == "dm" and self._allowed_users and user_id not in self._allowed_users:
            logger.debug("[%s] User %s not in allowlist", self.name, user_id)
            return
        if chat_type == "group" and self._group_allowed_users and user_id not in self._group_allowed_users:
            logger.debug("[%s] User %s not in group allowlist", self.name, user_id)
            return

        chat_id = str(data.get("group_id", data.get("author", {}).get("id", "")))

        source = self.build_source(
            chat_id=chat_id,
            user_id=user_id,
            user_name=user_name,
            chat_type=chat_type,
        )

        content = data.get("content", "")
        # Strip @mention from content
        mentions = data.get("mentions", [])
        for mention in mentions:
            bot_id = mention.get("id", "")
            if bot_id == self.app_id:
                content = content.replace(f"<@!{bot_id}>", "").strip()

        event = MessageEvent(
            text=content,
            message_type=MessageType.TEXT,
            source=source,
            raw_message=data,
            message_id=msg_id,
        )

        await self.handle_message(event)

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        return {"name": "QQ Chat", "type": "dm"}
