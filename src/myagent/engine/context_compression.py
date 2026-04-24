"""Context compression and token optimization for MyAgent.

Provides strategies to reduce token usage in long conversations:
- Message summarization
- Sliding window truncation
- Semantic compression
- Token counting
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from myagent.engine.messages import ConversationMessage, TextBlock, ToolResultBlock, ToolUseBlock

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Estimate token count for text.

    Uses a simple heuristic: ~4 characters per token for English/Chinese mixed text.
    For production, use tiktoken or the provider's tokenizer.
    """
    if not text:
        return 0
    # Rough estimate: English ~4 chars/token, Chinese ~1.5 chars/token
    # Mixed content average ~3 chars/token
    return max(1, len(text) // 3)


def estimate_message_tokens(msg: ConversationMessage) -> int:
    """Estimate tokens for a conversation message."""
    total = 0
    for block in msg.content:
        if isinstance(block, TextBlock):
            total += estimate_tokens(block.text)
        elif isinstance(block, ToolUseBlock):
            total += estimate_tokens(block.name)
            total += estimate_tokens(str(block.input))
        elif isinstance(block, ToolResultBlock):
            total += estimate_tokens(block.content)
    # Add overhead for message structure
    return total + 4


# ---------------------------------------------------------------------------
# Compression strategies
# ---------------------------------------------------------------------------

@dataclass
class CompressionResult:
    """Result of a compression operation."""

    messages: List[ConversationMessage]
    tokens_before: int
    tokens_after: int
    strategy_used: str


class ContextCompressor:
    """Compress conversation context to fit within token limits."""

    def __init__(
        self,
        max_tokens: int = 8000,
        preserve_recent: int = 4,
        summarizer: Optional[Callable[[List[ConversationMessage]], str]] = None,
    ) -> None:
        self.max_tokens = max_tokens
        self.preserve_recent = preserve_recent
        self.summarizer = summarizer

    def compress(self, messages: List[ConversationMessage]) -> CompressionResult:
        """Compress messages to fit within max_tokens.

        Tries strategies in order:
        1. If under limit, return as-is
        2. Truncate old tool results
        3. Summarize old messages
        4. Sliding window (drop oldest)
        """
        tokens_before = sum(estimate_message_tokens(m) for m in messages)

        if tokens_before <= self.max_tokens:
            return CompressionResult(
                messages=list(messages),
                tokens_before=tokens_before,
                tokens_after=tokens_before,
                strategy_used="none",
            )

        # Strategy 1: Truncate tool results
        result = self._truncate_tool_results(messages)
        tokens_after = sum(estimate_message_tokens(m) for m in result)
        if tokens_after <= self.max_tokens:
            return CompressionResult(
                messages=result,
                tokens_before=tokens_before,
                tokens_after=tokens_after,
                strategy_used="truncate_tools",
            )

        # Strategy 2: Summarize old messages
        if self.summarizer:
            result = self._summarize_old_messages(messages)
            tokens_after = sum(estimate_message_tokens(m) for m in result)
            if tokens_after <= self.max_tokens:
                return CompressionResult(
                    messages=result,
                    tokens_before=tokens_before,
                    tokens_after=tokens_after,
                    strategy_used="summarize",
                )

        # Strategy 3: Sliding window
        result = self._sliding_window(messages)
        tokens_after = sum(estimate_message_tokens(m) for m in result)
        return CompressionResult(
            messages=result,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            strategy_used="sliding_window",
        )

    def _truncate_tool_results(
        self, messages: List[ConversationMessage]
    ) -> List[ConversationMessage]:
        """Truncate long tool result outputs while preserving structure."""
        result = []
        for msg in messages:
            new_msg = ConversationMessage(role=msg.role, content=[])
            for block in msg.content:
                if isinstance(block, ToolResultBlock):
                    content = block.content
                    # Truncate very long outputs
                    if len(content) > 2000:
                        content = content[:1000] + "\n... [truncated] ...\n" + content[-500:]
                    new_msg.content.append(
                        ToolResultBlock(
                            tool_use_id=block.tool_use_id,
                            content=content,
                            is_error=block.is_error,
                        )
                    )
                else:
                    new_msg.content.append(block)
            result.append(new_msg)
        return result

    def _summarize_old_messages(
        self, messages: List[ConversationMessage]
    ) -> List[ConversationMessage]:
        """Summarize old messages, keeping recent ones intact."""
        if len(messages) <= self.preserve_recent + 1:
            return list(messages)

        # Keep system message and recent messages
        system_msg = None
        for msg in messages:
            if msg.role == "system":
                system_msg = msg
                break

        recent = messages[-self.preserve_recent :]
        old = messages[1:-self.preserve_recent] if system_msg else messages[:-self.preserve_recent]

        if not old:
            return list(messages)

        # Create summary
        if self.summarizer:
            summary_text = self.summarizer(old)
        else:
            summary_text = self._default_summarize(old)

        summary_msg = ConversationMessage.from_system_text(
            f"Previous conversation summary: {summary_text}"
        )

        result = []
        if system_msg:
            result.append(system_msg)
        result.append(summary_msg)
        result.extend(recent)
        return result

    def _default_summarize(self, messages: List[ConversationMessage]) -> str:
        """Default summarization: extract key topics and actions."""
        topics = []
        actions = []

        for msg in messages:
            text = msg.text
            if not text:
                continue
            # Extract first sentence as topic
            first_sentence = text.split(".")[0][:100]
            if first_sentence:
                topics.append(first_sentence)
            # Look for tool uses
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    actions.append(f"Used {block.name}")

        summary_parts = []
        if topics:
            summary_parts.append(f"Discussed: {'; '.join(topics[:3])}")
        if actions:
            summary_parts.append(f"Actions: {'; '.join(set(actions))}")

        return " | ".join(summary_parts) if summary_parts else "Previous context"

    def _sliding_window(
        self, messages: List[ConversationMessage]
    ) -> List[ConversationMessage]:
        """Keep only the most recent messages within token limit."""
        # Always keep system message
        system_msg = None
        for msg in messages:
            if msg.role == "system":
                system_msg = msg
                break

        # Start from the end and keep messages until we hit the limit
        result = []
        if system_msg:
            result.append(system_msg)

        current_tokens = sum(estimate_message_tokens(m) for m in result)
        # Reserve tokens for response
        available = self.max_tokens - current_tokens - 1000

        for msg in reversed(messages):
            if msg.role == "system":
                continue
            msg_tokens = estimate_message_tokens(msg)
            if current_tokens + msg_tokens > available:
                break
            result.insert(1 if system_msg else 0, msg)
            current_tokens += msg_tokens

        return result


# ---------------------------------------------------------------------------
# Auto-compaction integration
# ---------------------------------------------------------------------------

@dataclass
class TokenUsageStats:
    """Statistics for token usage monitoring."""

    total_tokens: int = 0
    tokens_per_turn: List[int] = None
    compression_count: int = 0
    last_compression_time: float = 0.0
    peak_tokens: int = 0

    def __post_init__(self):
        if self.tokens_per_turn is None:
            self.tokens_per_turn = []

    def record_turn(self, tokens: int) -> None:
        """Record token usage for a turn."""
        self.tokens_per_turn.append(tokens)
        self.total_tokens += tokens
        if tokens > self.peak_tokens:
            self.peak_tokens = tokens
        # Keep only last 20 turns
        if len(self.tokens_per_turn) > 20:
            self.tokens_per_turn.pop(0)

    @property
    def avg_tokens_per_turn(self) -> float:
        """Average tokens per turn over recent history."""
        if not self.tokens_per_turn:
            return 0.0
        return sum(self.tokens_per_turn) / len(self.tokens_per_turn)

    @property
    def token_growth_rate(self) -> float:
        """Rate of token growth (tokens per turn)."""
        if len(self.tokens_per_turn) < 2:
            return 0.0
        # Simple linear growth rate
        first = self.tokens_per_turn[0]
        last = self.tokens_per_turn[-1]
        return (last - first) / len(self.tokens_per_turn)


class AutoCompactor:
    """Automatically compact conversation when it grows too large.

    Features:
    - Dynamic threshold adjustment based on token growth rate
    - Preserves critical decision points (tool uses with errors)
    - Token usage statistics tracking
    """

    def __init__(
        self,
        compressor: ContextCompressor,
        threshold_ratio: float = 0.8,
        min_threshold_ratio: float = 0.5,
        max_threshold_ratio: float = 0.9,
    ) -> None:
        self.compressor = compressor
        self.threshold_ratio = threshold_ratio
        self.min_threshold_ratio = min_threshold_ratio
        self.max_threshold_ratio = max_threshold_ratio
        self.stats = TokenUsageStats()
        self._dynamic_threshold = threshold_ratio

    def _update_dynamic_threshold(self) -> None:
        """Adjust threshold based on token growth rate.

        If tokens are growing fast, lower the threshold to compact earlier.
        If tokens are stable, raise the threshold to compact less frequently.
        """
        growth_rate = self.stats.token_growth_rate
        if growth_rate > 30:  # Fast growth
            self._dynamic_threshold = max(
                self.min_threshold_ratio,
                self._dynamic_threshold - 0.05,
            )
        elif growth_rate < 5:  # Slow/stable growth
            self._dynamic_threshold = min(
                self.max_threshold_ratio,
                self._dynamic_threshold + 0.02,
            )

    def should_compact(self, messages: List[ConversationMessage]) -> bool:
        """Check if compaction is needed."""
        total_tokens = sum(estimate_message_tokens(m) for m in messages)
        self._update_dynamic_threshold()
        threshold = self.compressor.max_tokens * self._dynamic_threshold
        return total_tokens > threshold

    def compact(self, messages: List[ConversationMessage]) -> CompressionResult:
        """Compact messages if needed, preserving critical decision points."""
        tokens_before = sum(estimate_message_tokens(m) for m in messages)

        if not self.should_compact(messages):
            return CompressionResult(
                messages=list(messages),
                tokens_before=tokens_before,
                tokens_after=tokens_before,
                strategy_used="none",
            )

        # Pre-processing: identify critical messages to preserve
        critical_indices = self._identify_critical_messages(messages)

        # Compress non-critical messages first
        result = self._compress_with_preservation(messages, critical_indices)
        tokens_after = sum(estimate_message_tokens(m) for m in result)

        # Update stats
        self.stats.compression_count += 1
        self.stats.last_compression_time = time.time()

        strategy = "preserve_critical"
        if tokens_after > self.compressor.max_tokens * 0.9:
            # Still too large, fall back to full compression
            full_result = self.compressor.compress(result)
            tokens_after = full_result.tokens_after
            result = full_result.messages
            strategy = f"preserve_critical+{full_result.strategy_used}"

        return CompressionResult(
            messages=result,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            strategy_used=strategy,
        )

    def _identify_critical_messages(self, messages: List[ConversationMessage]) -> set:
        """Identify messages that should be preserved during compression.

        Critical messages include:
        - System prompt
        - Tool uses that resulted in errors
        - User messages with explicit commands
        """
        critical = set()
        for i, msg in enumerate(messages):
            if msg.role == "system":
                critical.add(i)
                continue
            # Check for tool results with errors
            for block in msg.content:
                if isinstance(block, ToolResultBlock) and block.is_error:
                    # Mark this message and the previous tool use as critical
                    critical.add(i)
                    if i > 0:
                        critical.add(i - 1)
                    break
            # Check for user commands
            if msg.role == "user" and msg.text:
                text = msg.text.strip().lower()
                if text.startswith(("/", "!", "#")):
                    critical.add(i)
        return critical

    def _compress_with_preservation(
        self, messages: List[ConversationMessage], critical_indices: set
    ) -> List[ConversationMessage]:
        """Compress messages while preserving critical ones."""
        # Separate critical and non-critical messages
        critical_msgs = [(i, m) for i, m in enumerate(messages) if i in critical_indices]
        non_critical = [(i, m) for i, m in enumerate(messages) if i not in critical_indices]

        if not non_critical:
            return list(messages)

        # Compress only non-critical messages
        _, non_critical_msgs = zip(*non_critical) if non_critical else ([], [])
        compressed = self.compressor.compress(list(non_critical_msgs))

        # Rebuild message list preserving order
        result = []
        critical_idx = 0
        compressed_idx = 0

        for i in range(len(messages)):
            if i in critical_indices:
                if critical_idx < len(critical_msgs):
                    result.append(critical_msgs[critical_idx][1])
                    critical_idx += 1
            else:
                if compressed_idx < len(compressed.messages):
                    result.append(compressed.messages[compressed_idx])
                    compressed_idx += 1

        return result

    def get_stats(self) -> TokenUsageStats:
        """Get token usage statistics."""
        return self.stats
