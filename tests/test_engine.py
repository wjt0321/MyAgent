"""Tests for myagent engine."""

import pytest

from myagent.engine.messages import (
    ConversationMessage,
    ImageBlock,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
)
from myagent.engine.stream_events import (
    AssistantTextDelta,
    AssistantTurnComplete,
    ErrorEvent,
    StatusEvent,
    StreamEvent,
    ToolExecutionCompleted,
    ToolExecutionStarted,
)


class TestMessageTypes:
    def test_text_block_creation(self):
        block = TextBlock(text="Hello world")
        assert block.text == "Hello world"
        assert block.type == "text"

    def test_tool_use_block_creation(self):
        block = ToolUseBlock(id="tool_1", name="Read", input={"path": "/tmp/test.txt"})
        assert block.id == "tool_1"
        assert block.name == "Read"
        assert block.input == {"path": "/tmp/test.txt"}
        assert block.type == "tool_use"

    def test_tool_result_block_creation(self):
        block = ToolResultBlock(tool_use_id="tool_1", content="file contents")
        assert block.tool_use_id == "tool_1"
        assert block.content == "file contents"
        assert block.is_error is False
        assert block.type == "tool_result"

    def test_tool_result_block_with_error(self):
        block = ToolResultBlock(
            tool_use_id="tool_1", content="Error: file not found", is_error=True
        )
        assert block.is_error is True

    def test_conversation_message_from_user_text(self):
        msg = ConversationMessage.from_user_text("Hello")
        assert msg.role == "user"
        assert len(msg.content) == 1
        assert isinstance(msg.content[0], TextBlock)
        assert msg.content[0].text == "Hello"

    def test_conversation_message_text_property(self):
        msg = ConversationMessage.from_user_text("Hello")
        assert msg.text == "Hello"

    def test_conversation_message_with_tool_use(self):
        msg = ConversationMessage(
            role="assistant",
            content=[ToolUseBlock(id="t1", name="Bash", input={"command": "ls"})],
        )
        assert msg.role == "assistant"
        assert msg.tool_uses == ["t1"]


class TestStreamEvents:
    def test_assistant_text_delta(self):
        event = AssistantTextDelta(text="Hello")
        assert event.text == "Hello"
        assert isinstance(event, StreamEvent)

    def test_tool_execution_started(self):
        event = ToolExecutionStarted(
            tool_name="Read", tool_use_id="t1", arguments={"path": "/tmp/test.txt"}
        )
        assert event.tool_name == "Read"
        assert event.tool_use_id == "t1"
        assert event.arguments == {"path": "/tmp/test.txt"}

    def test_tool_execution_completed(self):
        event = ToolExecutionCompleted(
            tool_use_id="t1", result="file contents", is_error=False
        )
        assert event.tool_use_id == "t1"
        assert event.result == "file contents"
        assert event.is_error is False

    def test_error_event(self):
        event = ErrorEvent(error=ValueError("test error"), recoverable=True)
        assert isinstance(event.error, ValueError)
        assert event.recoverable is True

    def test_status_event(self):
        event = StatusEvent(message="Working...")
        assert event.message == "Working..."

    def test_assistant_turn_complete(self):
        msg = ConversationMessage.from_user_text("Done")
        event = AssistantTurnComplete(message=msg)
        assert event.message == msg
