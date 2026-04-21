"""Shared helper classes for gateway platform adapters.

Extracts common patterns: message deduplication, text batch aggregation,
markdown stripping, and thread participation tracking.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, Optional

if TYPE_CHECKING:
    from myagent.gateway.base import MessageEvent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Message Deduplication
# ---------------------------------------------------------------------------

class MessageDeduplicator:
    """TTL-based message deduplication cache.

    Usage::

        dedup = MessageDeduplicator()
        if dedup.is_duplicate(msg_id):
            return
    """

    def __init__(self, max_size: int = 2000, ttl_seconds: float = 300):
        self._seen: Dict[str, float] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds

    def is_duplicate(self, msg_id: str | None) -> bool:
        """Return True if *msg_id* was already seen within the TTL window."""
        if not msg_id:
            return False
        now = time.time()
        if msg_id in self._seen:
            if now - self._seen[msg_id] < self._ttl:
                return True
            del self._seen[msg_id]
        self._seen[msg_id] = now
        if len(self._seen) > self._max_size:
            # Remove oldest entries to get back to max_size
            sorted_items = sorted(self._seen.items(), key=lambda x: x[1])
            self._seen = dict(sorted_items[-self._max_size :])
        return False

    def clear(self) -> None:
        """Clear all tracked messages."""
        self._seen.clear()


# ---------------------------------------------------------------------------
# Text Batch Aggregation
# ---------------------------------------------------------------------------

class TextBatchAggregator:
    """Aggregates rapid-fire text events into single messages.

    Usage::

        batcher = TextBatchAggregator(handler=message_handler, batch_delay=0.6)
        if event.message_type == MessageType.TEXT and batcher.is_enabled():
            batcher.enqueue(event, session_key)
            return
    """

    def __init__(
        self,
        handler: Callable[["MessageEvent"], asyncio.Future] | None,
        *,
        batch_delay: float = 0.6,
        split_delay: float = 2.0,
        split_threshold: int = 4000,
    ):
        self._handler = handler
        self._batch_delay = batch_delay
        self._split_delay = split_delay
        self._split_threshold = split_threshold
        self._pending: Dict[str, "MessageEvent"] = {}
        self._pending_tasks: Dict[str, asyncio.Task] = {}

    def is_enabled(self) -> bool:
        """Return True if batching is active (delay > 0)."""
        return self._batch_delay > 0

    def enqueue(self, event: "MessageEvent", key: str) -> None:
        """Add *event* to the pending batch for *key*."""
        chunk_len = len(event.text or "")
        existing = self._pending.get(key)
        if not existing:
            event._last_chunk_len = chunk_len  # type: ignore[attr-defined]
            self._pending[key] = event
        else:
            existing.text = f"{existing.text}\n{event.text}"
            existing._last_chunk_len = chunk_len  # type: ignore[attr-defined]

        prior = self._pending_tasks.get(key)
        if prior and not prior.done():
            prior.cancel()
        self._pending_tasks[key] = asyncio.create_task(self._flush(key))

    async def _flush(self, key: str) -> None:
        """Wait then dispatch the batched event for *key*."""
        current_task = self._pending_tasks.get(key)
        pending = self._pending.get(key)
        last_len = getattr(pending, "_last_chunk_len", 0) if pending else 0

        delay = self._split_delay if last_len >= self._split_threshold else self._batch_delay
        await asyncio.sleep(delay)

        event = self._pending.pop(key, None)
        if event and self._handler is not None:
            try:
                await self._handler(event)
            except Exception:
                logger.exception("[TextBatchAggregator] Error dispatching batched event for %s", key)

        if self._pending_tasks.get(key) is current_task:
            self._pending_tasks.pop(key, None)

    def cancel_all(self) -> None:
        """Cancel all pending flush tasks."""
        for task in self._pending_tasks.values():
            if not task.done():
                task.cancel()
        self._pending_tasks.clear()
        self._pending.clear()


# ---------------------------------------------------------------------------
# Thread Participation Tracking
# ---------------------------------------------------------------------------

class ThreadParticipationTracker:
    """Persistent tracking of threads the bot has participated in."""

    def __init__(self, platform_name: str, max_tracked: int = 500):
        self._platform = platform_name
        self._max_tracked = max_tracked
        self._threads: set = set()
        self._load()

    def _state_path(self) -> Path:
        from myagent.gateway.config import _get_myagent_home

        return _get_myagent_home() / f"{self._platform}_threads.json"

    def _load(self) -> None:
        path = self._state_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self._threads = set(data)
            except Exception:
                self._threads = set()

    def _save(self) -> None:
        path = self._state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        thread_list = list(self._threads)
        if len(thread_list) > self._max_tracked:
            # Keep only the most recently added items
            thread_list = thread_list[-self._max_tracked :]
        self._threads = set(thread_list)
        path.write_text(json.dumps(thread_list), encoding="utf-8")

    def mark(self, thread_id: str) -> None:
        """Mark *thread_id* as participated and persist."""
        if thread_id not in self._threads:
            self._threads.add(thread_id)
            self._save()

    def __contains__(self, thread_id: str) -> bool:
        return thread_id in self._threads

    def clear(self) -> None:
        self._threads.clear()
        self._save()
