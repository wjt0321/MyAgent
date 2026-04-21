"""Remote bridge for MyAgent cross-network communication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Coroutine


@dataclass
class RemoteMessage:
    """A message sent/received over the remote bridge."""

    type: str
    payload: dict[str, Any]
    sender: str
    timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "payload": self.payload,
            "sender": self.sender,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RemoteMessage | None:
        try:
            return cls(
                type=data.get("type", "unknown"),
                payload=data.get("payload", {}),
                sender=data.get("sender", "unknown"),
                timestamp=data.get("timestamp"),
            )
        except Exception:
            return None


MessageHandler = Callable[[RemoteMessage], Coroutine[Any, Any, None]]


class RemoteBridge:
    """Lightweight remote bridge for agent-to-agent communication."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9000) -> None:
        self.host = host
        self.port = port
        self.running = False
        self._handlers: list[MessageHandler] = []
        self._outbox: list[RemoteMessage] = []

    def on_message(self, handler: MessageHandler) -> None:
        """Register a message handler."""
        self._handlers.append(handler)

    async def start(self) -> None:
        """Start the remote bridge."""
        self.running = True

    async def stop(self) -> None:
        """Stop the remote bridge."""
        self.running = False

    async def send(self, message: RemoteMessage) -> None:
        """Send a message over the bridge."""
        if not self.running:
            raise RuntimeError("Bridge is not running")
        self._outbox.append(message)

    async def _handle_incoming(self, data: dict[str, Any]) -> None:
        """Handle an incoming message."""
        message = RemoteMessage.from_dict(data)
        if message is None:
            return

        for handler in self._handlers:
            await handler(message)

    def get_outbox(self) -> list[RemoteMessage]:
        """Get messages queued for sending."""
        return list(self._outbox)

    def clear_outbox(self) -> None:
        """Clear the outbox."""
        self._outbox = []
