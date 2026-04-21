"""QueryEngine for MyAgent."""

from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncIterator

from myagent.engine.messages import (
    ConversationMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
)
from myagent.engine.stream_events import (
    AssistantTextDelta,
    AssistantTurnComplete,
    ErrorEvent,
    StreamEvent,
    ToolExecutionCompleted,
    ToolExecutionStarted,
)
from myagent.llm.base import BaseProvider
from myagent.llm.types import DoneChunk, TextChunk, ToolUseChunk
from myagent.tools.base import ToolExecutionContext
from myagent.tools.registry import ToolRegistry


class MaxTurnsExceeded(Exception):
    """Raised when the agent exceeds the maximum number of turns."""


class QueryEngine:
    """Core engine that owns the conversation history and tool-aware loop."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        system_prompt: str = "You are a helpful assistant.",
        max_turns: int = 50,
        auto_compact_threshold: float | None = None,
        llm_client: BaseProvider | None = None,
    ) -> None:
        self.tool_registry = tool_registry
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self.auto_compact_threshold = auto_compact_threshold
        self.llm_client = llm_client
        self.messages: list[ConversationMessage] = [
            ConversationMessage.from_system_text(system_prompt)
        ]
        self._turn_count = 0

    async def submit_message(
        self, prompt: str | ConversationMessage
    ) -> AsyncIterator[StreamEvent]:
        """Submit a user message and run the query loop."""
        if isinstance(prompt, str):
            prompt = ConversationMessage.from_user_text(prompt)
        self.messages.append(prompt)

        async for event in self._run_loop():
            yield event

    async def _run_loop(self) -> AsyncIterator[StreamEvent]:
        """Run the tool-aware conversation loop."""
        while True:
            if self._turn_count >= self.max_turns:
                raise MaxTurnsExceeded(
                    f"Maximum number of turns ({self.max_turns}) exceeded."
                )
            self._turn_count += 1

            if self.llm_client is None:
                yield ErrorEvent(
                    error=RuntimeError("No LLM client configured."),
                    recoverable=False,
                )
                return

            assistant_message = ConversationMessage(role="assistant", content=[])
            current_tool_use: ToolUseBlock | None = None

            async for chunk in self.llm_client.stream_messages(
                self.messages,
                self.tool_registry.to_api_schema(),
            ):
                if isinstance(chunk, TextChunk):
                    assistant_message.content.append(TextBlock(text=chunk.text))
                    yield AssistantTextDelta(text=chunk.text)

                elif isinstance(chunk, ToolUseChunk):
                    tool_use = ToolUseBlock(
                        id=chunk.id,
                        name=chunk.name,
                        input=chunk.input,
                    )
                    assistant_message.content.append(tool_use)
                    current_tool_use = tool_use
                    yield ToolExecutionStarted(
                        tool_name=tool_use.name,
                        tool_use_id=tool_use.id,
                        arguments=tool_use.input,
                    )

                elif isinstance(chunk, DoneChunk):
                    break

            self.messages.append(assistant_message)

            if current_tool_use is None:
                yield AssistantTurnComplete(message=assistant_message)
                return

            tool = self.tool_registry.get(current_tool_use.name)
            if tool is None:
                result = ToolResult(
                    output=f"Error: Tool '{current_tool_use.name}' not found.",
                    is_error=True,
                )
            else:
                try:
                    parsed = tool.input_model.model_validate(current_tool_use.input)
                    ctx = ToolExecutionContext(cwd=Path.cwd())
                    result = await tool.execute(parsed, ctx)
                except Exception as e:
                    result = ToolResult(output=f"Error: {e}", is_error=True)

            self.messages.append(
                ConversationMessage(
                    role="user",
                    content=[
                        ToolResultBlock(
                            tool_use_id=current_tool_use.id,
                            content=result.output,
                            is_error=result.is_error,
                        )
                    ],
                )
            )

            yield ToolExecutionCompleted(
                tool_use_id=current_tool_use.id,
                result=result.output,
                is_error=result.is_error,
            )
