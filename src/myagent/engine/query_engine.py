"""QueryEngine for MyAgent."""

from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncIterator, Callable

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
    PermissionRequestEvent,
    PermissionResultEvent,
    StreamEvent,
    ToolExecutionCompleted,
    ToolExecutionStarted,
)
from myagent.llm.base import BaseProvider
from myagent.llm.types import DoneChunk, TextChunk, ToolUseChunk
from myagent.security.checker import PermissionChecker, PermissionLevel
from myagent.tools.base import ToolExecutionContext, ToolResult
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
        permission_checker: PermissionChecker | None = None,
    ) -> None:
        self.tool_registry = tool_registry
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self.auto_compact_threshold = auto_compact_threshold
        self.llm_client = llm_client
        self.permission_checker = permission_checker or PermissionChecker()
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

            permission_result = self.permission_checker.check(
                current_tool_use.name,
                current_tool_use.input,
            )

            if permission_result.level == PermissionLevel.DENY:
                result = ToolResult(
                    output=f"Permission denied: {permission_result.reason}",
                    is_error=True,
                )
                yield PermissionResultEvent(
                    tool_name=current_tool_use.name,
                    approved=False,
                    reason=permission_result.reason,
                )
            elif permission_result.level == PermissionLevel.ASK:
                yield PermissionRequestEvent(
                    tool_name=current_tool_use.name,
                    arguments=current_tool_use.input,
                    reason=permission_result.reason,
                )
                return
            else:
                result = await self._execute_tool(current_tool_use)

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

    async def continue_with_permission(
        self, tool_use_id: str, approved: bool
    ) -> AsyncIterator[StreamEvent]:
        """Continue the loop after user grants or denies permission."""
        assistant_message = self.messages[-1]
        current_tool_use = None

        for block in assistant_message.content:
            if isinstance(block, ToolUseBlock) and block.id == tool_use_id:
                current_tool_use = block
                break

        if current_tool_use is None:
            yield ErrorEvent(
                error=RuntimeError(f"Tool use {tool_use_id} not found."),
                recoverable=False,
            )
            return

        if approved:
            result = await self._execute_tool(current_tool_use)
            yield PermissionResultEvent(
                tool_name=current_tool_use.name,
                approved=True,
                reason="User approved",
            )
        else:
            result = ToolResult(
                output="Permission denied by user.",
                is_error=True,
            )
            yield PermissionResultEvent(
                tool_name=current_tool_use.name,
                approved=False,
                reason="User denied",
            )

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

        async for event in self._run_loop():
            yield event

    async def _execute_tool(self, tool_use: ToolUseBlock) -> ToolResult:
        """Execute a tool and return the result."""
        tool = self.tool_registry.get(tool_use.name)
        if tool is None:
            return ToolResult(
                output=f"Error: Tool '{tool_use.name}' not found.",
                is_error=True,
            )

        try:
            parsed = tool.input_model.model_validate(tool_use.input)
            ctx = ToolExecutionContext(cwd=Path.cwd())
            return await tool.execute(parsed, ctx)
        except Exception as e:
            return ToolResult(output=f"Error: {e}", is_error=True)
