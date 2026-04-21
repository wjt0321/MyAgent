"""Legacy gateway adapter base class for MyAgent.

Kept for backward compatibility. Use BasePlatformAdapter for new code.
"""

from __future__ import annotations

from typing import Any, Callable, Coroutine

from myagent.gateway.base import GatewayMessage

MessageHandler = Callable[[GatewayMessage], Coroutine[Any, Any, None]]


class GatewayAdapter:
    """Abstract base class for gateway adapters (legacy).

    Kept for backward compatibility. New code should use BasePlatformAdapter.
    """

    name: str = "abstract"

    def __init__(self) -> None:
        self._handlers: list[MessageHandler] = []
        self.running = False

    def on_message(self, handler: MessageHandler) -> None:
        """Register a message handler."""
        self._handlers.append(handler)

    async def _notify_handlers(self, message: GatewayMessage) -> None:
        """Notify all registered handlers of a message."""
        for handler in self._handlers:
            await handler(message)

    async def start(self) -> None:
        """Start the gateway adapter."""
        self.running = True

    async def stop(self) -> None:
        """Stop the gateway adapter."""
        self.running = False

    async def send(self, message: GatewayMessage) -> None:
        """Send a message through the gateway."""
        pass
