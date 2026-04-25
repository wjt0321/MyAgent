"""Tests for gateway bot."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from myagent.config.settings import Settings
from myagent.engine.messages import ConversationMessage
from myagent.engine.stream_events import (
    AssistantTextDelta,
    AssistantTurnComplete,
    PermissionRequestEvent,
)
from myagent.gateway.base import MessageEvent, Platform, SessionSource
from myagent.gateway.bot import GatewayBot
from myagent.gateway.config import GatewayConfig


class TestGatewayBot:
    def test_creation(self):
        bot = GatewayBot(config=GatewayConfig(), settings=Settings())
        assert bot.config is not None
        assert bot.manager is not None
        assert bot.get_session_count() == 0

    def test_stats_empty(self):
        bot = GatewayBot(config=GatewayConfig(), settings=Settings())
        stats = bot.get_stats()
        assert stats["active_sessions"] == 0
        assert stats["connected_platforms"] == []

    def test_load_agents(self):
        bot = GatewayBot(config=GatewayConfig(), settings=Settings())
        # Should load built-in agents if available
        assert bot._default_agent is not None

    @pytest.mark.asyncio
    async def test_handle_message_command_reset(self):
        bot = GatewayBot(config=GatewayConfig(), settings=Settings())
        source = SessionSource(platform=Platform.TELEGRAM, chat_id="123", user_id="u1")
        event = MessageEvent(text="/reset", source=source)

        response = await bot._handle_message(event)
        assert "reset" in response.lower()

    @pytest.mark.asyncio
    async def test_handle_message_command_help(self):
        bot = GatewayBot(config=GatewayConfig(), settings=Settings())
        source = SessionSource(platform=Platform.TELEGRAM, chat_id="123", user_id="u1")
        event = MessageEvent(text="/help", source=source)

        response = await bot._handle_message(event)
        assert "help" in response.lower()
        assert "/reset" in response

    @pytest.mark.asyncio
    async def test_handle_message_command_agent(self):
        bot = GatewayBot(config=GatewayConfig(), settings=Settings())
        source = SessionSource(platform=Platform.TELEGRAM, chat_id="123", user_id="u1")
        event = MessageEvent(text="/agent", source=source)

        response = await bot._handle_message(event)
        assert response is not None
        assert "agent" in response.lower() or "available" in response.lower()

    @pytest.mark.asyncio
    async def test_handle_message_no_source(self):
        bot = GatewayBot(config=GatewayConfig(), settings=Settings())
        event = MessageEvent(text="hello", source=None)
        response = await bot._handle_message(event)
        assert response is None

    @pytest.mark.asyncio
    async def test_busy_handler(self):
        bot = GatewayBot(config=GatewayConfig(), settings=Settings())
        source = SessionSource(platform=Platform.TELEGRAM, chat_id="123", user_id="u1")
        event = MessageEvent(text="hello", source=source)

        result = await bot._busy_handler(event, "telegram:123:u1")
        assert result is False  # Default lets base adapter handle it

    @pytest.mark.asyncio
    async def test_permission_resume_uses_event_tool_use_id(self):
        """权限恢复时应使用事件上的 tool_use_id。"""
        bot = GatewayBot(config=GatewayConfig(), settings=Settings())
        source = SessionSource(platform=Platform.TELEGRAM, chat_id="123", user_id="u1")
        event = MessageEvent(text="hello", source=source)
        captured: list[tuple[str, bool]] = []

        class FakeEngine:
            async def submit_message(self, prompt: str):
                yield PermissionRequestEvent(
                    tool_name="bash",
                    tool_use_id="tool-456",
                    arguments={"command": "rm -rf ."},
                    reason="需要审批",
                )

            async def continue_with_permission(self, tool_use_id: str, approved: bool):
                captured.append((tool_use_id, approved))
                yield AssistantTextDelta(text="继续执行")
                yield AssistantTurnComplete(
                    message=ConversationMessage.from_assistant_text("继续执行"),
                )

        bot._get_or_create_session = lambda *args, **kwargs: FakeEngine()
        bot._handle_permission_request = AsyncMock(return_value=True)

        response = await bot._handle_message(event)

        assert response == "继续执行"
        assert captured == [("tool-456", True)]
