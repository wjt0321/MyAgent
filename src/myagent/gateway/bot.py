"""Gateway Bot for MyAgent.

Connects platform adapters to QueryEngine for full agent capabilities
across messaging platforms.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from myagent.agents.definitions import AgentDefinition
from myagent.agents.loader import AgentLoader
from myagent.config.settings import Settings
from myagent.cost.tracker import CostTracker
from myagent.engine.query_engine import QueryEngine
from myagent.gateway.adapter_base import BasePlatformAdapter
from myagent.gateway.base import (
    MessageEvent,
    MessageType,
    Platform,
    ProcessingOutcome,
)
from myagent.gateway.config import GatewayConfig, load_gateway_config
from myagent.gateway.manager import GatewayManager
from myagent.gateway.session_store import GatewaySessionStore
from myagent.llm.base import BaseProvider
from myagent.llm.registry import ProviderRegistry
from myagent.security.checker import PermissionChecker
from myagent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class GatewayBot:
    """Bot that runs QueryEngine across messaging platforms."""

    def __init__(
        self,
        config: GatewayConfig | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.config = config or load_gateway_config()
        self.settings = settings or Settings.load()
        self.manager = GatewayManager(self.config)

        # Agent state
        self._agents: Dict[str, AgentDefinition] = {}
        self._default_agent = "general"
        self._sessions: Dict[str, QueryEngine] = {}
        self._session_platforms: Dict[str, Platform] = {}

        # Persistent session store for user-session bindings
        self._session_store = GatewaySessionStore()

        # Initialize core components
        self.tool_registry = ToolRegistry.with_core_tools()
        self.permission_checker = PermissionChecker()
        self.cost_tracker = CostTracker()
        self.provider_registry = ProviderRegistry.with_defaults()

        # Load agents
        self._load_agents()

    def _load_agents(self) -> None:
        """Load built-in agents."""
        loader = AgentLoader()
        self._agents = loader.load_builtin_agents()
        if self._agents:
            self._default_agent = list(self._agents.keys())[0]
            logger.info("Loaded %d agents", len(self._agents))

    def _get_llm_client(self) -> BaseProvider | None:
        """Get LLM client from settings."""
        provider_name = self.settings.default_provider
        if not provider_name:
            return None
        provider_cls = self.provider_registry.get(provider_name)
        if not provider_cls:
            return None
        return provider_cls()

    def _get_or_create_session(
        self, session_key: str, platform: Platform, user_id: str | None = None, chat_id: str | None = None
    ) -> QueryEngine:
        """Get or create a QueryEngine session.

        If user_id and chat_id are provided, attempts to restore a persisted session.
        """
        # Check for persisted session if user info is available
        if user_id and chat_id:
            persisted_id = self._session_store.get_session_id(platform, user_id, chat_id)
            if persisted_id and persisted_id in self._sessions:
                logger.debug("Restored persisted session: %s", persisted_id)
                return self._sessions[persisted_id]

        if session_key not in self._sessions:
            agent = self._agents.get(self._default_agent)
            system_prompt = agent.system_prompt if agent else "You are a helpful assistant."

            engine = QueryEngine(
                tool_registry=self.tool_registry,
                system_prompt=system_prompt,
                llm_client=self._get_llm_client(),
                permission_checker=self.permission_checker,
            )
            self._sessions[session_key] = engine
            self._session_platforms[session_key] = platform

            # Persist the binding if user info is available
            if user_id and chat_id:
                self._session_store.bind_session(
                    platform=platform,
                    user_id=user_id,
                    chat_id=chat_id,
                    session_id=session_key,
                    agent=self._default_agent,
                )

            logger.debug("Created new session: %s", session_key)
        return self._sessions[session_key]

    async def _handle_message(self, event: MessageEvent) -> Optional[str]:
        """Handle an incoming message event."""
        if not event.source:
            return None

        session_key = event.source.session_key
        platform = event.source.platform

        # Handle commands
        cmd = event.get_command()
        if cmd == "reset" or cmd == "new":
            if session_key in self._sessions:
                del self._sessions[session_key]
            # Unbind persisted session
            if event.source and event.source.user_id:
                self._session_store.unbind_session(
                    platform=event.source.platform,
                    user_id=event.source.user_id,
                    chat_id=event.source.chat_id,
                )
            return "🔄 Session reset. Starting fresh!"

        if cmd == "agent":
            args = event.get_command_args()
            if args in self._agents:
                # Switch agent for this session
                if session_key in self._sessions:
                    del self._sessions[session_key]
                self._default_agent = args
                return f"🤖 Switched to **{args}** agent."
            available = ", ".join(f"`{k}`" for k in self._agents.keys())
            return f"Available agents: {available}"

        if cmd == "help":
            return (
                "**MyAgent Bot Commands:**\n"
                "• `/reset` — Start a fresh session\n"
                "• `/agent <name>` — Switch agent\n"
                "• `/help` — Show this help\n"
                "\nJust send a message to chat!"
            )

        # Get or create session (with user info for persistence)
        user_id = event.source.user_id if event.source else None
        chat_id = event.source.chat_id if event.source else None
        engine = self._get_or_create_session(session_key, platform, user_id=user_id, chat_id=chat_id)

        # Build prompt with media context
        prompt = event.text
        if event.media_urls:
            media_desc = "\n".join(f"[Media: {url}]" for url in event.media_urls)
            prompt = f"{prompt}\n\n{media_desc}"

        # Collect response
        response_parts: list[str] = []
        try:
            async for stream_event in engine.submit_message(prompt):
                from myagent.engine.stream_events import (
                    AssistantTextDelta,
                    AssistantTurnComplete,
                    ErrorEvent,
                    PermissionRequestEvent,
                    PermissionResultEvent,
                    ToolExecutionStarted,
                    ToolExecutionCompleted,
                )

                if isinstance(stream_event, AssistantTextDelta):
                    response_parts.append(stream_event.text)
                elif isinstance(stream_event, AssistantTurnComplete):
                    break
                elif isinstance(stream_event, ErrorEvent):
                    return f"❌ Error: {stream_event.error}"
                elif isinstance(stream_event, PermissionRequestEvent):
                    # Route permission request to the platform adapter
                    approved = await self._handle_permission_request(event, stream_event)
                    if approved:
                        # Continue with the tool execution
                        async for cont_event in engine.continue_with_permission(
                            stream_event.tool_use_id,
                            approved=True,
                        ):
                            if isinstance(cont_event, AssistantTextDelta):
                                response_parts.append(cont_event.text)
                            elif isinstance(cont_event, AssistantTurnComplete):
                                break
                            elif isinstance(cont_event, ErrorEvent):
                                return f"❌ Error: {cont_event.error}"
                    else:
                        # User denied permission
                        async for cont_event in engine.continue_with_permission(
                            stream_event.tool_use_id,
                            approved=False,
                        ):
                            if isinstance(cont_event, AssistantTextDelta):
                                response_parts.append(cont_event.text)
                            elif isinstance(cont_event, AssistantTurnComplete):
                                break
                elif isinstance(stream_event, ToolExecutionStarted):
                    # Could send typing indicator here
                    pass
        except Exception as e:
            logger.error("Error in session %s: %s", session_key, e, exc_info=True)
            return f"❌ Sorry, an error occurred: {e}"

        return "".join(response_parts) if response_parts else None

    async def _handle_permission_request(
        self,
        event: MessageEvent,
        permission_event: Any,
    ) -> bool:
        """Route a permission request to the appropriate platform adapter.

        Returns True if approved, False otherwise.
        """
        from myagent.engine.stream_events import PermissionRequestEvent

        if not isinstance(permission_event, PermissionRequestEvent):
            return False

        if not event.source:
            return False

        adapter = self.manager.get_adapter(event.source.platform)
        if adapter is None:
            logger.warning("No adapter found for platform %s", event.source.platform)
            return False

        # Check if adapter supports permission requests
        if hasattr(adapter, "send_permission_request"):
            try:
                return await adapter.send_permission_request(
                    chat_id=event.source.chat_id,
                    tool_name=permission_event.tool_name,
                    arguments=permission_event.arguments,
                    reason=permission_event.reason,
                )
            except Exception as e:
                logger.error("Permission request failed: %s", e)
                return False
        else:
            # Fallback: auto-deny if adapter doesn't support permissions
            logger.warning(
                "[%s] Adapter does not support permission requests, auto-denying",
                adapter.name,
            )
            return False

    async def _busy_handler(self, event: MessageEvent, session_key: str) -> bool:
        """Handle messages arriving during active sessions.

        Returns True if the message was handled and should not interrupt.
        """
        # By default, let the base adapter handle interrupts
        # Subclasses can override for custom behavior
        return False

    async def start(self) -> None:
        """Start the bot."""
        logger.info("Starting Gateway Bot...")

        # Set up message routing
        self.manager.set_message_handler(self._handle_message)
        self.manager.set_busy_session_handler(self._busy_handler)

        # Auto-create adapters from config
        self.manager.create_from_config()

        # Start all adapters
        await self.manager.start_all()

        connected = self.manager.connected_platforms
        if connected:
            names = [p.value for p in connected]
            logger.info("Gateway Bot running on: %s", ", ".join(names))
        else:
            logger.warning("No platforms connected. Check your configuration.")

        # Keep running
        while self.manager._running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop the bot gracefully."""
        logger.info("Stopping Gateway Bot...")
        await self.manager.stop_all()
        self._sessions.clear()

    def get_session_count(self) -> int:
        """Get the number of active sessions."""
        return len(self._sessions)

    def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        return {
            "connected_platforms": [p.value for p in self.manager.connected_platforms],
            "active_sessions": len(self._sessions),
            "loaded_agents": list(self._agents.keys()),
            "default_agent": self._default_agent,
        }
