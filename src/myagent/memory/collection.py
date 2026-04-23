"""Memory auto-collection system.

Uses LLM to analyze conversations and automatically extract memories.
Supports incremental collection, deduplication, and batch processing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from myagent.memory.manager import MemoryEntry, MemoryManager, MemoryType


MEMORY_EXTRACTION_PROMPT = """You are a memory extraction system. Analyze the following conversation and extract any important information that should be remembered for future interactions.

Guidelines:
- Extract user preferences, background, habits
- Note feedback about what works well or poorly
- Record project context and decisions
- Capture external references and resources
- Only extract factual, durable information (not temporary details)
- Avoid extracting information already covered in existing memories

Output format (JSON array):
[
  {
    "name": "Short descriptive name",
    "description": "One-line summary",
    "type": "user|feedback|project|reference",
    "content": "Detailed memory content (2-5 sentences)"
  }
]

If no new memories should be extracted, return an empty array [].

Existing memories (do not duplicate):
{existing_memories}

Conversation to analyze:
---
{conversation}
---

Extracted memories:"""


class MemoryCollector:
    """Automatically collects memories from conversations."""

    def __init__(self, memory_manager: MemoryManager) -> None:
        self.memory_manager = memory_manager
        self._pending_conversations: list[str] = []
        self._min_messages_for_extraction = 4
        self._max_pending_length = 8000

    def add_conversation(self, user_message: str, assistant_response: str) -> None:
        """Add a conversation turn to the pending buffer."""
        self._pending_conversations.append(
            f"USER: {user_message}\nASSISTANT: {assistant_response}"
        )

    def should_extract(self, message_count: int) -> bool:
        """Check if we have enough messages to trigger extraction."""
        return message_count >= self._min_messages_for_extraction

    def extract_memories(
        self,
        conversation: str,
        llm_client: Any,
        existing: list[MemoryEntry] | None = None,
    ) -> list[MemoryEntry]:
        """Extract memories from a conversation using LLM.

        Args:
            conversation: The conversation text to analyze
            llm_client: LLM client for extraction
            existing: Existing memories to avoid duplication

        Returns:
            List of extracted memory entries
        """
        existing_summary = ""
        if existing:
            existing_summary = "\n".join(
                f"- {e.name}: {e.description}" for e in existing[:10]
            )

        prompt = MEMORY_EXTRACTION_PROMPT.format(
            conversation=conversation,
            existing_memories=existing_summary or "None",
        )

        try:
            response = llm_client.complete(prompt)
            # Clean up response - sometimes LLM wraps in markdown
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            data = json.loads(response)

            entries = []
            for item in data:
                entry = MemoryEntry(
                    name=item["name"],
                    description=item["description"],
                    type=MemoryType(item["type"]),
                    content=item["content"],
                )
                entries.append(entry)

            return entries
        except Exception:
            return []

    def save_extracted_memories(self, entries: list[MemoryEntry]) -> list[Path]:
        """Save extracted memories to disk with deduplication.

        Args:
            entries: List of memory entries to save

        Returns:
            List of paths to saved memory files
        """
        paths = []
        for entry in entries:
            # Check if similar memory already exists by name
            existing = self.memory_manager.get_memory(entry.name)
            if existing:
                # Merge content instead of overwriting
                merged = self._merge_memory(existing, entry)
                path = self.memory_manager.save_memory(merged)
            else:
                path = self.memory_manager.save_memory(entry)
            paths.append(path)
        return paths

    def _merge_memory(self, existing: MemoryEntry, new: MemoryEntry) -> MemoryEntry:
        """Merge new memory into existing one."""
        # Simple merge: append new content with timestamp note
        merged_content = existing.content
        if new.content not in existing.content:
            merged_content += f"\n\n[Updated] {new.content}"
        return MemoryEntry(
            name=existing.name,
            description=new.description or existing.description,
            type=new.type if new.type != MemoryType.USER else existing.type,
            content=merged_content,
        )

    def collect_from_session(
        self,
        messages: list[dict[str, str]],
        llm_client: Any,
    ) -> list[Path]:
        """Collect memories from a session's messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            llm_client: LLM client for extraction

        Returns:
            List of paths to saved memory files
        """
        conversation = "\n\n".join(
            f"{msg['role'].upper()}: {msg['content']}" for msg in messages
        )

        existing = self.memory_manager.list_memories()
        entries = self.extract_memories(conversation, llm_client, existing)
        return self.save_extracted_memories(entries)

    def collect_from_turn(
        self,
        user_message: str,
        assistant_response: str,
        llm_client: Any,
    ) -> list[Path]:
        """Collect memories from a single conversation turn.

        This is the primary method for real-time memory collection.
        It buffers conversations and only triggers extraction when enough
        content has accumulated.

        Args:
            user_message: User's message
            assistant_response: Assistant's response
            llm_client: LLM client for extraction

        Returns:
            List of paths to saved memory files (empty if not triggered)
        """
        self.add_conversation(user_message, assistant_response)

        # Check if we should trigger extraction
        total_length = sum(len(c) for c in self._pending_conversations)
        if total_length < self._max_pending_length:
            return []

        # Build conversation text from pending buffer
        conversation = "\n\n---\n\n".join(self._pending_conversations)

        # Get existing memories for deduplication
        existing = self.memory_manager.list_memories()

        # Extract memories
        entries = self.extract_memories(conversation, llm_client, existing)
        paths = self.save_extracted_memories(entries)

        # Clear pending buffer
        self._pending_conversations = []

        return paths

    def flush(self, llm_client: Any) -> list[Path]:
        """Force extraction of any pending conversations.

        Args:
            llm_client: LLM client for extraction

        Returns:
            List of paths to saved memory files
        """
        if not self._pending_conversations:
            return []

        conversation = "\n\n---\n\n".join(self._pending_conversations)
        existing = self.memory_manager.list_memories()
        entries = self.extract_memories(conversation, llm_client, existing)
        paths = self.save_extracted_memories(entries)
        self._pending_conversations = []
        return paths
