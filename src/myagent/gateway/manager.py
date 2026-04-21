"""Gateway manager for MyAgent.

Manages multiple platform adapters, routes messages to QueryEngine,
and handles session lifecycle.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from myagent.gateway.adapter_base import BasePlatformAdapter
from myagent.gateway.base import (
    GatewayMessage,
    MessageEvent,
    MessageHandler,
    Platform,
    ProcessingOutcome,
)
from myagent.gateway.config import GatewayConfig, PlatformConfig, load_gateway_config

logger = logging.getLogger(__name__)


class GatewayManager:
    """Manages multiple gateway adapters and routes messages."""

    def __init__(self, config: GatewayConfig | None = None) -> None:
        self.config = config or load_gateway_config()
        self.adapters: Dict[Platform, BasePlatformAdapter] = {}
        self._message_handler: MessageHandler | None = None
        self._busy_session_handler: Callable[[MessageEvent, str], Awaitable[bool]] | None = None
        self._running = False

    def register_adapter(self, adapter: BasePlatformAdapter) -> None:
        """Register a platform adapter."""
        self.adapters[adapter.platform] = adapter
        if self._message_handler:
            adapter.set_message_handler(self._message_handler)
        if self._busy_session_handler:
            adapter.set_busy_session_handler(self._busy_session_handler)
        logger.info("[%s] Adapter registered", adapter.name)

    def set_message_handler(self, handler: MessageHandler) -> None:
        """Set the global message handler for all adapters."""
        self._message_handler = handler
        for adapter in self.adapters.values():
            adapter.set_message_handler(handler)

    def set_busy_session_handler(
        self, handler: Callable[[MessageEvent, str], Awaitable[bool]]
    ) -> None:
        """Set handler for messages arriving during active sessions."""
        self._busy_session_handler = handler
        for adapter in self.adapters.values():
            adapter.set_busy_session_handler(handler)

    async def start_all(self) -> None:
        """Start all registered adapters."""
        self._running = True
        for platform, adapter in self.adapters.items():
            try:
                success = await adapter.connect()
                if not success:
                    logger.error("[%s] Failed to connect", adapter.name)
            except Exception as e:
                logger.error("[%s] Connection error: %s", adapter.name, e)

    async def stop_all(self) -> None:
        """Stop all adapters gracefully."""
        self._running = False
        for adapter in self.adapters.values():
            try:
                await adapter.cancel_background_tasks()
                await adapter.disconnect()
            except Exception as e:
                logger.error("[%s] Disconnect error: %s", adapter.name, e)

    async def broadcast(self, text: str, platforms: List[Platform] | None = None) -> None:
        """Broadcast a message to all connected platforms."""
        targets = platforms or list(self.adapters.keys())
        for platform in targets:
            adapter = self.adapters.get(platform)
            if not adapter or not adapter.is_connected:
                continue
            config = self.config.platforms.get(platform)
            if not config or not config.home_channel:
                continue
            try:
                await adapter.send(
                    chat_id=config.home_channel.chat_id,
                    content=text,
                )
            except Exception as e:
                logger.error("[%s] Broadcast failed: %s", adapter.name, e)

    def get_adapter(self, platform: Platform) -> BasePlatformAdapter | None:
        """Get an adapter by platform."""
        return self.adapters.get(platform)

    @property
    def connected_platforms(self) -> List[Platform]:
        """List currently connected platforms."""
        return [
            p for p, a in self.adapters.items()
            if a.is_connected
        ]

    def create_from_config(self) -> None:
        """Auto-create and register adapters from config."""
        from myagent.gateway.adapters.discord import DiscordAdapter
        from myagent.gateway.adapters.feishu import FeishuAdapter
        from myagent.gateway.adapters.qq import QQAdapter
        from myagent.gateway.adapters.slack import SlackAdapter
        from myagent.gateway.adapters.telegram import TelegramAdapter
        from myagent.gateway.adapters.weixin import WeixinAdapter

        adapter_map = {
            Platform.DISCORD: DiscordAdapter,
            Platform.TELEGRAM: TelegramAdapter,
            Platform.SLACK: SlackAdapter,
            Platform.FEISHU: FeishuAdapter,
            Platform.WEIXIN: WeixinAdapter,
            Platform.QQ: QQAdapter,
        }

        for platform in self.config.get_connected_platforms():
            adapter_cls = adapter_map.get(platform)
            if not adapter_cls:
                continue
            config = self.config.platforms.get(platform)
            if not config:
                continue
            try:
                adapter = adapter_cls(config)
                self.register_adapter(adapter)
            except Exception as e:
                logger.error("Failed to create adapter for %s: %s", platform.value, e)
