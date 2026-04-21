"""Stream parser utilities for MyAgent LLM providers."""

from __future__ import annotations

import json
from typing import Any, Iterator


class SSEParser:
    """Parser for Server-Sent Events (SSE) streams."""

    def parse_lines(self, lines: list[str]) -> Iterator[dict[str, Any]]:
        """Parse SSE lines into JSON events."""
        for line in lines:
            line = line.strip()
            if not line or not line.startswith("data: "):
                continue

            data = line[6:]
            if data == "[DONE]":
                continue

            try:
                event = json.loads(data)
                yield event
            except json.JSONDecodeError:
                continue
