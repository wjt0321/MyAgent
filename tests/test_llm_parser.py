"""Tests for LLM stream parser."""

from __future__ import annotations

import pytest

from myagent.llm.stream_parser import SSEParser
from myagent.llm.types import DoneChunk, TextChunk, ToolUseChunk


class TestSSEParser:
    def test_parse_sse_text_line(self):
        parser = SSEParser()
        lines = ["data: {\"type\": \"text\", \"text\": \"Hello\"}", ""]
        events = list(parser.parse_lines(lines))
        assert len(events) == 1
        assert events[0] == {"type": "text", "text": "Hello"}

    def test_parse_sse_done_line(self):
        parser = SSEParser()
        lines = ["data: [DONE]", ""]
        events = list(parser.parse_lines(lines))
        assert len(events) == 0  # [DONE] is filtered by parser

    def test_parse_sse_empty_line(self):
        parser = SSEParser()
        lines = ["", "event: message", "data: {}"]
        events = list(parser.parse_lines(lines))
        assert len(events) == 1

    def test_parse_sse_multiline(self):
        parser = SSEParser()
        lines = [
            "data: {\"type\": \"text\"}",
            "",
            "data: {\"type\": \"done\"}",
            "",
        ]
        events = list(parser.parse_lines(lines))
        assert len(events) == 2

    def test_parse_sse_invalid_json(self):
        parser = SSEParser()
        lines = ["data: not json", ""]
        events = list(parser.parse_lines(lines))
        assert len(events) == 0  # Invalid JSON is skipped

    def test_parse_sse_no_data_prefix(self):
        parser = SSEParser()
        lines = ["{\"type\": \"text\"}", ""]
        events = list(parser.parse_lines(lines))
        assert len(events) == 0  # Lines without data: prefix are skipped
