"""Memory extraction and RAG retrieval for MyAgent.

This module provides:
- MemoryExtractor: Automatically identifies key information in conversations
- MemoryRAG: Retrieves relevant memories to enhance context
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myagent.memory.manager import MemoryEntry


@dataclass
class ExtractedMemory:
    """A piece of information extracted from conversation."""
    content: str
    type: str
    importance: float
    reasoning: str


class MemoryExtractor:
    """Extracts key information from conversations for memory storage.

    This is a lightweight heuristic-based extractor. For production use,
    an LLM-based extraction would be more accurate.
    """

    PATTERNS = [
        (r"(?:我的|用户|I\s+)?名字(?:叫|是)[：:]?\s*(\S+)", "user_name", 0.8),
        (r"(?:我|用户)?(?:的)?邮箱(?:是)?[：:]?\s*(\S+@\S+)", "email", 0.9),
        (r"(?:我的|用户)?电话(?:码)?(?:是)?[：:]?\s*(\d{7,})", "phone", 0.9),
        (r"(?:我的|用户)?公司(?:是)?[：:]?\s*(\S+)", "company", 0.7),
        (r"(?:我的|用户)?职位(?:是)?[：:]?\s*(\S+)", "job_title", 0.7),
        (r"使用\s*(\S+)\s*(?:语言|框架|库|工具)", "tech_stack", 0.6),
        (r"偏好[：:]\s*(.+?)(?:\n|$)", "preference", 0.5),
        (r"(?:记住|记一下|save)\s*[:：]\s*(.+?)(?:\n|$)", "manual_memory", 0.95),
    ]

    def __init__(self, min_importance: float = 0.6) -> None:
        self.min_importance = min_importance

    def extract(self, text: str) -> list[ExtractedMemory]:
        """Extract potential memories from text."""
        memories = []
        for pattern, mem_type, importance in self.PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) > 0:
                    content = match.group(1).strip()
                    if len(content) >= 2 and len(content) <= 200:
                        memories.append(ExtractedMemory(
                            content=content,
                            type=mem_type,
                            importance=importance,
                            reasoning=f"Matched pattern: {pattern[:30]}...",
                        ))
        return [m for m in memories if m.importance >= self.min_importance]

    def extract_from_messages(self, messages: list) -> list[ExtractedMemory]:
        """Extract from a list of conversation messages."""
        all_memories = []
        for msg in messages:
            if hasattr(msg, 'text') and msg.text:
                memories = self.extract(msg.text)
                all_memories.extend(memories)
            elif hasattr(msg, 'content'):
                for block in msg.content:
                    if hasattr(block, 'text') and block.text:
                        memories = self.extract(block.text)
                        all_memories.extend(memories)
        return all_memories


class MemoryRAG:
    """Retrieval-Augmented Memory for context enhancement."""

    def __init__(self, memory_manager) -> None:
        self.memory_manager = memory_manager
        self.extractor = MemoryExtractor()

    def retrieve(self, query: str, max_memories: int = 5) -> str | None:
        """Retrieve relevant memories for a query."""
        memories = self.memory_manager.list_memories()
        if not memories:
            return None

        query_lower = query.lower()
        scored_memories: list[tuple[float, "MemoryEntry"]] = []

        for entry in memories:
            score = 0.0
            query_words = set(query_lower.split())
            content_words = set(entry.content.lower().split())
            name_words = set(entry.name.lower().split())

            overlap = query_words & content_words
            score += len(overlap) * 0.3

            name_overlap = query_words & name_words
            score += len(name_overlap) * 0.5

            if entry.type.value in query_lower:
                score += 0.4

            if scored_memories or name_overlap:
                score += 0.2

            scored_memories.append((score, entry))

        scored_memories.sort(key=lambda x: x[0], reverse=True)
        top_memories = [entry for _, entry in scored_memories[:max_memories]]

        if not top_memories:
            return None

        lines = ["# Relevant Memories"]
        for entry in top_memories:
            lines.extend([
                f"## {entry.name}",
                f"[{entry.type.value}]",
                "",
                entry.content[:500],
                "",
            ])

        return "\n".join(lines)

    def suggest_memory(self, messages: list, threshold: int = 10) -> list[ExtractedMemory]:
        """Suggest memories based on conversation length.

        Args:
            messages: List of conversation messages
            threshold: Minimum number of messages before suggesting memories

        Returns:
            List of suggested memory extractions
        """
        if len(messages) < threshold:
            return []

        return self.extractor.extract_from_messages(messages)
