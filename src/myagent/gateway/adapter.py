"""Gateway adapter base class for MyAgent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Coroutine


@dataclass
class GatewayMessage:
    """A message received from or sent to a gateway platform."""

    text: str
    user_id: str
    channel_id: str
    platform: str
    raw_data: dict[str, Any] | None = None

    def reply(self, text: str) -> GatewayMessage:
        """Create a reply message."""
        return GatewayMessage(
            text=text,
            user_id="agent",
            channel_id=self.channel_id,
            platform=self.platform,
        )


MessageHandler = Callable[[GatewayMessage], Coroutine[Any, Any, None]]


class GatewayAdapter(ABC):
    """Abstract base class for gateway adapters."""

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

    @abstractmethod
    async def start(self) -> None:
        """Start the gateway adapter."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the gateway adapter."""
        ...

    @abstractmethod
    async def send(self, message: GatewayMessage) -> None:
        """Send a message through the gateway."""
        ...
