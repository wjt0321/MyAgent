"""Tests for gateway helper utilities."""

from __future__ import annotations

import asyncio
import time

import pytest

from myagent.gateway.helpers import (
    MessageDeduplicator,
    TextBatchAggregator,
    ThreadParticipationTracker,
)
from myagent.gateway.base import MessageEvent, MessageType, SessionSource, Platform


class TestMessageDeduplicator:
    def test_new_message_not_duplicate(self):
        dedup = MessageDeduplicator()
        assert dedup.is_duplicate("msg_1") is False

    def test_duplicate_within_ttl(self):
        dedup = MessageDeduplicator(ttl_seconds=60)
        dedup.is_duplicate("msg_1")
        assert dedup.is_duplicate("msg_1") is True

    def test_not_duplicate_after_ttl(self):
        dedup = MessageDeduplicator(ttl_seconds=0.01)
        dedup.is_duplicate("msg_1")
        time.sleep(0.02)
        assert dedup.is_duplicate("msg_1") is False

    def test_empty_id_not_duplicate(self):
        dedup = MessageDeduplicator()
        assert dedup.is_duplicate("") is False
        assert dedup.is_duplicate(None) is False

    def test_max_size_cleanup(self):
        dedup = MessageDeduplicator(max_size=3, ttl_seconds=60)
        dedup.is_duplicate("a")
        time.sleep(0.01)
        dedup.is_duplicate("b")
        time.sleep(0.01)
        dedup.is_duplicate("c")
        time.sleep(0.01)
        dedup.is_duplicate("d")  # Should trigger cleanup
        assert len(dedup._seen) <= 3

    def test_clear(self):
        dedup = MessageDeduplicator()
        dedup.is_duplicate("msg_1")
        dedup.clear()
        assert dedup.is_duplicate("msg_1") is False


class TestTextBatchAggregator:
    @pytest.mark.asyncio
    async def test_enqueue_and_flush(self):
        handler_calls = []

        async def handler(event):
            handler_calls.append(event)

        aggregator = TextBatchAggregator(handler=handler, batch_delay=0.05)
        source = SessionSource(platform=Platform.DISCORD, chat_id="123")
        event = MessageEvent(text="hello", source=source)

        aggregator.enqueue(event, "key1")
        assert "key1" in aggregator._pending

        await asyncio.sleep(0.1)
        assert len(handler_calls) == 1
        assert handler_calls[0].text == "hello"

    @pytest.mark.asyncio
    async def test_batch_merge(self):
        handler_calls = []

        async def handler(event):
            handler_calls.append(event)

        aggregator = TextBatchAggregator(handler=handler, batch_delay=0.05)
        source = SessionSource(platform=Platform.DISCORD, chat_id="123")

        aggregator.enqueue(MessageEvent(text="hello", source=source), "key1")
        aggregator.enqueue(MessageEvent(text="world", source=source), "key1")

        await asyncio.sleep(0.1)
        assert len(handler_calls) == 1
        assert "hello" in handler_calls[0].text
        assert "world" in handler_calls[0].text

    @pytest.mark.asyncio
    async def test_cancel_all(self):
        handler_calls = []

        async def handler(event):
            handler_calls.append(event)

        aggregator = TextBatchAggregator(handler=handler, batch_delay=0.5)
        source = SessionSource(platform=Platform.DISCORD, chat_id="123")

        aggregator.enqueue(MessageEvent(text="hello", source=source), "key1")
        aggregator.cancel_all()

        await asyncio.sleep(0.1)
        assert len(handler_calls) == 0

    def test_disabled_when_zero_delay(self):
        aggregator = TextBatchAggregator(handler=None, batch_delay=0)
        assert aggregator.is_enabled() is False


class TestThreadParticipationTracker:
    def test_mark_and_contains(self):
        tracker = ThreadParticipationTracker("test_platform_unique_123")
        tracker.mark("thread_1")
        assert "thread_1" in tracker

    def test_not_contains_unmarked(self):
        tracker = ThreadParticipationTracker("test_platform_unique_456")
        assert "thread_1" not in tracker

    def test_clear(self):
        tracker = ThreadParticipationTracker("test_platform_unique_789")
        tracker.mark("thread_1")
        tracker.clear()
        assert "thread_1" not in tracker

    def test_max_tracked_limit(self):
        tracker = ThreadParticipationTracker("test_platform_unique_jkl", max_tracked=3)
        for i in range(5):
            tracker.mark(f"thread_{i}")
            time.sleep(0.02)
        # After adding 5 items with max_tracked=3, at most 3 should remain
        assert len(tracker._threads) <= 3
        # The last item should always be present (since we just added it)
        assert "thread_4" in tracker
