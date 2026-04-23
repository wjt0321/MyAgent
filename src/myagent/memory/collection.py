"""Memory auto-collection system.

Uses LLM to analyze conversations and automatically extract memories.
"""

from __future__ import annotations

import json
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

Conversation to analyze:
---
{conversation}
---

Extracted memories:"""


class MemoryCollector:
    """Automatically collects memories from conversations."""

    def __init__(self, memory_manager: MemoryManager) -> None:
        self.memory_manager = memory_manager

    def extract_memories(self, conversation: str, llm_client: Any) -> list[MemoryEntry]:
        """Extract memories from a conversation using LLM.

        Args:
            conversation: The conversation text to analyze
            llm_client: LLM client for extraction

        Returns:
            List of extracted memory entries
        """
        prompt = MEMORY_EXTRACTION_PROMPT.format(conversation=conversation)

        try:
            response = llm_client.complete(prompt)
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
        """Save extracted memories to disk.

        Args:
            entries: List of memory entries to save

        Returns:
            List of paths to saved memory files
        """
        paths = []
        for entry in entries:
            # Check if similar memory already exists
            existing = self.memory_manager.get_memory(entry.name)
            if existing:
                # Update existing memory
                existing.content = entry.content
                existing.description = entry.description
                existing.type = entry.type
                path = self.memory_manager.save_memory(existing)
            else:
                path = self.memory_manager.save_memory(entry)
            paths.append(path)
        return paths

    def collect_from_session(self, messages: list[dict[str, str]], llm_client: Any) -> list[Path]:
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

        entries = self.extract_memories(conversation, llm_client)
        return self.save_extracted_memories(entries)
