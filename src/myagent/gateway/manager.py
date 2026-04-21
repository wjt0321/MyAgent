"""Gateway manager for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.gateway.adapter import GatewayAdapter, GatewayMessage, MessageHandler


class GatewayManager:
    """Manages multiple gateway adapters."""

    def __init__(self) -> None:
        self.adapters: list[GatewayAdapter] = []
        self._handlers: list[MessageHandler] = []

    def register(self, adapter: GatewayAdapter) -> None:
        """Register a gateway adapter."""
        self.adapters.append(adapter)
        for handler in self._handlers:
            adapter.on_message(handler)

    def on_message(self, handler: MessageHandler) -> None:
        """Register a global message handler for all adapters."""
        self._handlers.append(handler)
        for adapter in self.adapters:
            adapter.on_message(handler)

    async def start_all(self) -> None:
        """Start all registered adapters."""
        for adapter in self.adapters:
            await adapter.start()

    async def stop_all(self) -> None:
        """Stop all registered adapters."""
        for adapter in self.adapters:
            await adapter.stop()

    async def broadcast(self, message: GatewayMessage) -> None:
        """Broadcast a message to all adapters."""
        for adapter in self.adapters:
            await adapter.send(message)
