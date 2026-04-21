"""Base platform adapter for MyAgent.

Production-ready abstract base with session management, retry logic,
media extraction, and interrupt support.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
import random
import re
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Optional

from myagent.gateway.base import (
    MessageEvent,
    MessageHandler,
    MessageType,
    Platform,
    ProcessingOutcome,
    SendResult,
    SessionSource,
    extract_images,
    is_retryable_error,
    is_timeout_error,
    strip_markdown,
    truncate_message,
)
from myagent.gateway.config import PlatformConfig

logger = logging.getLogger(__name__)


class BasePlatformAdapter(ABC):
    """Base class for platform adapters.

    Subclasses implement platform-specific logic for:
    - Connecting and authenticating
    - Receiving messages
    - Sending messages/responses
    - Handling media
    """

    REQUIRES_EDIT_FINALIZE: bool = False

    def __init__(self, config: PlatformConfig, platform: Platform) -> None:
        self.config = config
        self.platform = platform
        self._message_handler: Optional[MessageHandler] = None
        self._running = False
        self._fatal_error_code: Optional[str] = None
        self._fatal_error_message: Optional[str] = None
        self._fatal_error_retryable = True

        # Session tracking
        self._active_sessions: Dict[str, asyncio.Event] = {}
        self._pending_messages: Dict[str, MessageEvent] = {}
        self._background_tasks: set[asyncio.Task] = set()
        self._post_delivery_callbacks: Dict[str, Any] = {}
        self._expected_cancelled_tasks: set[asyncio.Task] = set()
        self._busy_session_handler: Optional[
            Callable[[MessageEvent, str], Awaitable[bool]]
        ] = None
        self._typing_paused: set = set()

    @property
    def name(self) -> str:
        """Human-readable name for this adapter."""
        return self.platform.value.title()

    @property
    def is_connected(self) -> bool:
        """Check if adapter is currently connected."""
        return self._running

    @property
    def has_fatal_error(self) -> bool:
        return self._fatal_error_message is not None

    @property
    def fatal_error_message(self) -> Optional[str]:
        return self._fatal_error_message

    @property
    def fatal_error_code(self) -> Optional[str]:
        return self._fatal_error_code

    @property
    def fatal_error_retryable(self) -> bool:
        return self._fatal_error_retryable

    def set_message_handler(self, handler: MessageHandler) -> None:
        """Set the handler for incoming messages."""
        self._message_handler = handler

    def set_busy_session_handler(
        self, handler: Optional[Callable[[MessageEvent, str], Awaitable[bool]]]
    ) -> None:
        """Set an optional handler for messages arriving during active sessions."""
        self._busy_session_handler = handler

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the platform and start receiving messages.

        Returns True if connection was successful.
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the platform."""
        ...

    @abstractmethod
    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        """Send a message to a chat."""
        ...

    async def edit_message(
        self,
        chat_id: str,
        message_id: str,
        content: str,
        *,
        finalize: bool = False,
    ) -> SendResult:
        """Edit a previously sent message."""
        return SendResult(success=False, error="Not supported")

    async def send_typing(self, chat_id: str, metadata: Any = None) -> None:
        """Send a typing indicator."""
        pass

    async def stop_typing(self, chat_id: str) -> None:
        """Stop a persistent typing indicator."""
        pass

    async def send_image(
        self,
        chat_id: str,
        image_url: str,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        """Send an image natively via the platform API."""
        text = f"{caption}\n{image_url}" if caption else image_url
        return await self.send(chat_id=chat_id, content=text, reply_to=reply_to)

    async def send_voice(
        self,
        chat_id: str,
        audio_path: str,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
        **kwargs: Any,
    ) -> SendResult:
        """Send an audio file as a native voice message."""
        text = f"🔊 Audio: {audio_path}"
        if caption:
            text = f"{caption}\n{text}"
        return await self.send(chat_id=chat_id, content=text, reply_to=reply_to)

    async def send_document(
        self,
        chat_id: str,
        file_path: str,
        caption: Optional[str] = None,
        file_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        **kwargs: Any,
    ) -> SendResult:
        """Send a document/file natively via the platform API."""
        text = f"📎 File: {file_path}"
        if caption:
            text = f"{caption}\n{text}"
        return await self.send(chat_id=chat_id, content=text, reply_to=reply_to)

    async def _send_with_retry(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Any = None,
        max_retries: int = 2,
        base_delay: float = 2.0,
    ) -> SendResult:
        """Send a message with automatic retry for transient network errors."""
        result = await self.send(
            chat_id=chat_id,
            content=content,
            reply_to=reply_to,
            metadata=metadata,
        )

        if result.success:
            return result

        error_str = result.error or ""
        is_network = result.retryable or is_retryable_error(error_str)

        if not is_network and is_timeout_error(error_str):
            return result

        if is_network:
            for attempt in range(1, max_retries + 1):
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                logger.warning(
                    "[%s] Send failed (attempt %d/%d, retrying in %.1fs): %s",
                    self.name, attempt, max_retries, delay, error_str,
                )
                await asyncio.sleep(delay)
                result = await self.send(
                    chat_id=chat_id,
                    content=content,
                    reply_to=reply_to,
                    metadata=metadata,
                )
                if result.success:
                    logger.info("[%s] Send succeeded on retry %d", self.name, attempt)
                    return result
                error_str = result.error or ""
                if not (result.retryable or is_retryable_error(error_str)):
                    break
            else:
                logger.error(
                    "[%s] Failed to deliver response after %d retries: %s",
                    self.name, max_retries, error_str,
                )
                notice = (
                    "⚠️ Message delivery failed after multiple attempts. "
                    "Please try again — your request was processed but the response could not be sent."
                )
                try:
                    await self.send(chat_id=chat_id, content=notice, reply_to=reply_to, metadata=metadata)
                except Exception as notify_err:
                    logger.debug("[%s] Could not send delivery-failure notice: %s", self.name, notify_err)
                return result

        # Plain-text fallback
        logger.warning("[%s] Send failed: %s — trying plain-text fallback", self.name, error_str)
        fallback_result = await self.send(
            chat_id=chat_id,
            content=f"(Response formatting failed, plain text:)\n\n{content[:3500]}",
            reply_to=reply_to,
            metadata=metadata,
        )
        if not fallback_result.success:
            logger.error("[%s] Fallback send also failed: %s", self.name, fallback_result.error)
        return fallback_result

    async def _keep_typing(
        self,
        chat_id: str,
        interval: float = 2.0,
        metadata: Any = None,
        stop_event: asyncio.Event | None = None,
    ) -> None:
        """Continuously send typing indicator until cancelled."""
        try:
            while True:
                if stop_event is not None and stop_event.is_set():
                    return
                if chat_id not in self._typing_paused:
                    await self.send_typing(chat_id, metadata=metadata)
                if stop_event is None:
                    await asyncio.sleep(interval)
                    continue
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=interval)
                except asyncio.TimeoutError:
                    continue
                return
        except asyncio.CancelledError:
            pass
        finally:
            if hasattr(self, "stop_typing"):
                try:
                    await self.stop_typing(chat_id)
                except Exception:
                    pass
            self._typing_paused.discard(chat_id)

    def pause_typing_for_chat(self, chat_id: str) -> None:
        """Pause typing indicator for a chat."""
        self._typing_paused.add(chat_id)

    def resume_typing_for_chat(self, chat_id: str) -> None:
        """Resume typing indicator for a chat."""
        self._typing_paused.discard(chat_id)

    async def interrupt_session_activity(self, session_key: str, chat_id: str) -> None:
        """Signal the active session loop to stop."""
        if session_key:
            interrupt_event = self._active_sessions.get(session_key)
            if interrupt_event is not None:
                interrupt_event.set()
        try:
            await self.stop_typing(chat_id)
        except Exception:
            pass

    def build_source(
        self,
        chat_id: str,
        chat_name: Optional[str] = None,
        chat_type: str = "dm",
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        thread_id: Optional[str] = None,
        chat_topic: Optional[str] = None,
        is_bot: bool = False,
    ) -> SessionSource:
        """Helper to build a SessionSource for this platform."""
        if chat_topic is not None and not chat_topic.strip():
            chat_topic = None
        return SessionSource(
            platform=self.platform,
            chat_id=str(chat_id),
            chat_name=chat_name,
            chat_type=chat_type,
            user_id=str(user_id) if user_id else None,
            user_name=user_name,
            thread_id=str(thread_id) if thread_id else None,
            chat_topic=chat_topic.strip() if chat_topic else None,
            is_bot=is_bot,
        )

    def format_message(self, content: str) -> str:
        """Format a message for this platform. Override in subclasses."""
        return content

    async def handle_message(self, event: MessageEvent) -> None:
        """Process an incoming message.

        Returns quickly by spawning background tasks for interruption support.
        """
        if not self._message_handler:
            return

        session_key = event.source.session_key if event.source else "unknown"

        # Check if there's already an active handler for this session
        if session_key in self._active_sessions:
            # Commands that bypass active session guard
            cmd = event.get_command()
            if cmd in ("stop", "new", "reset", "approve", "deny"):
                logger.debug("[%s] Command '/%s' bypassing active-session guard", self.name, cmd)
                try:
                    response = await self._message_handler(event)
                    if response:
                        await self._send_with_retry(
                            chat_id=event.source.chat_id if event.source else "",
                            content=response,
                            reply_to=event.message_id,
                        )
                except Exception as e:
                    logger.error("[%s] Command '/%s' dispatch failed: %s", self.name, cmd, e)
                return

            if self._busy_session_handler is not None:
                try:
                    if await self._busy_session_handler(event, session_key):
                        return
                except Exception as e:
                    logger.error("[%s] Busy-session handler failed: %s", self.name, e)

            # Photo bursts: queue without interrupting
            if event.message_type in (MessageType.PHOTO, MessageType.IMAGE):
                logger.debug("[%s] Queuing photo follow-up for session %s", self.name, session_key)
                self._pending_messages[session_key] = event
                return

            # Default: interrupt the running agent
            logger.debug("[%s] New message while session %s is active — triggering interrupt", self.name, session_key)
            self._pending_messages[session_key] = event
            self._active_sessions[session_key].set()
            return

        # Mark session as active before spawning background task
        self._active_sessions[session_key] = asyncio.Event()

        task = asyncio.create_task(self._process_message_background(event, session_key))
        try:
            self._background_tasks.add(task)
        except TypeError:
            return
        if hasattr(task, "add_done_callback"):
            task.add_done_callback(self._background_tasks.discard)
            task.add_done_callback(self._expected_cancelled_tasks.discard)

    async def _process_message_background(self, event: MessageEvent, session_key: str) -> None:
        """Background task that actually processes the message."""
        delivery_attempted = False
        delivery_succeeded = False

        def _record_delivery(result: SendResult | None) -> None:
            nonlocal delivery_attempted, delivery_succeeded
            if result is None:
                return
            delivery_attempted = True
            if getattr(result, "success", False):
                delivery_succeeded = True

        interrupt_event = self._active_sessions.get(session_key) or asyncio.Event()
        self._active_sessions[session_key] = interrupt_event

        typing_task = asyncio.create_task(
            self._keep_typing(
                event.source.chat_id if event.source else "",
                stop_event=interrupt_event,
            )
        )

        try:
            await self.on_processing_start(event)

            response = await self._message_handler(event)

            # Suppress stale response when interrupted
            if response and interrupt_event.is_set() and session_key in self._pending_messages:
                logger.info("[%s] Suppressing stale response for interrupted session %s", self.name, session_key)
                response = None

            if response:
                # Extract images
                images, text_content = extract_images(response)

                # Send text portion
                if text_content:
                    logger.info("[%s] Sending response (%d chars) to %s", self.name, len(text_content), event.source.chat_id if event.source else "")
                    result = await self._send_with_retry(
                        chat_id=event.source.chat_id if event.source else "",
                        content=text_content,
                        reply_to=event.message_id,
                    )
                    _record_delivery(result)

                # Send images
                for image_url, alt_text in images:
                    try:
                        img_result = await self.send_image(
                            chat_id=event.source.chat_id if event.source else "",
                            image_url=image_url,
                            caption=alt_text if alt_text else None,
                        )
                        if not img_result.success:
                            logger.error("[%s] Failed to send image: %s", self.name, img_result.error)
                    except Exception as img_err:
                        logger.error("[%s] Error sending image: %s", self.name, img_err)

            processing_ok = delivery_succeeded if delivery_attempted else not bool(response)
            await self.on_processing_complete(
                event,
                ProcessingOutcome.SUCCESS if processing_ok else ProcessingOutcome.FAILURE,
            )

            # Process pending message if any
            if session_key in self._pending_messages:
                pending_event = self._pending_messages.pop(session_key)
                logger.debug("[%s] Processing queued message from interrupt", self.name)
                _active = self._active_sessions.get(session_key)
                if _active is not None:
                    _active.clear()
                typing_task.cancel()
                try:
                    await typing_task
                except asyncio.CancelledError:
                    pass
                await self._process_message_background(pending_event, session_key)
                return

        except asyncio.CancelledError:
            await self.on_processing_complete(event, ProcessingOutcome.CANCELLED)
            raise
        except Exception as e:
            await self.on_processing_complete(event, ProcessingOutcome.FAILURE)
            logger.error("[%s] Error handling message: %s", self.name, e, exc_info=True)
            try:
                error_type = type(e).__name__
                await self.send(
                    chat_id=event.source.chat_id if event.source else "",
                    content=(
                        f"Sorry, I encountered an error ({error_type}).\n"
                        f"{str(e)[:300]}\n"
                        "Try again or use /reset to start a fresh session."
                    ),
                )
            except Exception:
                pass
        finally:
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass
            try:
                if hasattr(self, "stop_typing"):
                    await self.stop_typing(event.source.chat_id if event.source else "")
            except Exception:
                pass

            late_pending = self._pending_messages.pop(session_key, None)
            if late_pending is not None:
                logger.debug("[%s] Late-arrival pending message during cleanup", self.name)
                _active = self._active_sessions.get(session_key)
                if _active is not None:
                    _active.clear()
                drain_task = asyncio.create_task(
                    self._process_message_background(late_pending, session_key)
                )
                try:
                    self._background_tasks.add(drain_task)
                    drain_task.add_done_callback(self._background_tasks.discard)
                except TypeError:
                    pass
            else:
                if session_key in self._active_sessions:
                    del self._active_sessions[session_key]

    async def cancel_background_tasks(self) -> None:
        """Cancel any in-flight background message-processing tasks."""
        MAX_DRAIN_ROUNDS = 5
        for _ in range(MAX_DRAIN_ROUNDS):
            tasks = [task for task in self._background_tasks if not task.done()]
            if not tasks:
                break
            for task in tasks:
                self._expected_cancelled_tasks.add(task)
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        self._background_tasks.clear()
        self._expected_cancelled_tasks.clear()
        self._pending_messages.clear()
        self._active_sessions.clear()

    def has_pending_interrupt(self, session_key: str) -> bool:
        """Check if there's a pending interrupt for a session."""
        return session_key in self._active_sessions and self._active_sessions[session_key].is_set()

    def get_pending_message(self, session_key: str) -> Optional[MessageEvent]:
        """Get and clear any pending message for a session."""
        return self._pending_messages.pop(session_key, None)

    # -- Lifecycle hooks (subclasses override) --

    async def on_processing_start(self, event: MessageEvent) -> None:
        """Hook called when background processing begins."""
        pass

    async def on_processing_complete(self, event: MessageEvent, outcome: ProcessingOutcome) -> None:
        """Hook called when background processing completes."""
        pass

    @abstractmethod
    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """Get information about a chat/channel."""
        ...
