"""Webhook gateway adapter for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.gateway.adapter import GatewayAdapter, GatewayMessage


class WebhookGateway(GatewayAdapter):
    """Simple webhook-based gateway for HTTP callbacks."""

    name = "webhook"

    def __init__(self, host: str = "127.0.0.1", port: int = 8080) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self._pending_messages: list[GatewayMessage] = []

    async def start(self) -> None:
        """Start the webhook gateway."""
        self.running = True

    async def stop(self) -> None:
        """Stop the webhook gateway."""
        self.running = False

    async def send(self, message: GatewayMessage) -> None:
        """Queue a message for sending (placeholder for HTTP response)."""
        if not self.running:
            raise RuntimeError("Gateway is not running")
        self._pending_messages.append(message)

    async def _handle_incoming(self, data: dict[str, Any]) -> None:
        """Handle an incoming webhook payload."""
        if not self.running:
            return

        message = GatewayMessage(
            text=data.get("text", ""),
            user_id=data.get("user_id", "unknown"),
            channel_id=data.get("channel_id", "default"),
            platform="webhook",
            raw_data=data,
        )
        await self._notify_handlers(message)

    def get_pending_messages(self) -> list[GatewayMessage]:
        """Get messages queued for sending."""
        return list(self._pending_messages)
