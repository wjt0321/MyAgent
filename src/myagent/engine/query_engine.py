"""QueryEngine for MyAgent."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from myagent.engine.context_compression import AutoCompactor, ContextCompressor, estimate_message_tokens
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
from myagent.monitoring.metrics import get_registry
from myagent.security.checker import PermissionChecker, PermissionLevel
from myagent.tools.base import ToolExecutionContext, ToolResult
from myagent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


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

        # Initialize auto-compactor if threshold is set
        self.auto_compactor: AutoCompactor | None = None
        if auto_compact_threshold:
            compressor = ContextCompressor(max_tokens=8000)
            self.auto_compactor = AutoCompactor(
                compressor=compressor,
                threshold_ratio=auto_compact_threshold,
            )

        # Metrics
        self._metrics = get_registry()
        self._llm_latency_hist = self._metrics.histogram(
            "llm_request_duration_seconds", "LLM request latency"
        )
        self._tool_latency_hist = self._metrics.histogram(
            "tool_execution_duration_seconds", "Tool execution latency"
        )
        self._turn_counter = self._metrics.counter(
            "query_turns_total", "Total query turns"
        )
        self._tool_counter = self._metrics.counter(
            "tool_executions_total", "Total tool executions"
        )
        self._tool_error_counter = self._metrics.counter(
            "tool_errors_total", "Total tool execution errors"
        )
        self._error_counter = self._metrics.counter(
            "query_errors_total", "Total query errors"
        )
        self._token_gauge = self._metrics.gauge(
            "query_context_tokens", "Current context token count"
        )
        self._compression_counter = self._metrics.counter(
            "query_compactions_total", "Total context compactions"
        )

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
            # Check auto-compaction before each turn
            if self.auto_compactor and self.auto_compactor.should_compact(self.messages):
                result = self.auto_compactor.compact(self.messages)
                if result.strategy_used != "none":
                    self.messages = result.messages
                    yield AssistantTextDelta(
                        text=f"\n[Context auto-compacted: {result.tokens_before} -> {result.tokens_after} tokens ({result.strategy_used})]\n"
                    )

            # Record token usage stats
            current_tokens = sum(estimate_message_tokens(m) for m in self.messages)
            self._token_gauge.set(current_tokens)
            if self.auto_compactor:
                self.auto_compactor.stats.record_turn(current_tokens)
                self._compression_counter.set(self.auto_compactor.stats.compression_count)

            if self._turn_count >= self.max_turns:
                yield ErrorEvent(
                    error=MaxTurnsExceeded(
                        f"Maximum number of turns ({self.max_turns}) exceeded."
                    ),
                    recoverable=False,
                )
                return
            self._turn_count += 1
            self._turn_counter.inc()

            if self.llm_client is None:
                self._error_counter.inc()
                yield ErrorEvent(
                    error=RuntimeError("No LLM client configured."),
                    recoverable=False,
                )
                return

            assistant_message = ConversationMessage(role="assistant", content=[])
            current_tool_use: ToolUseBlock | None = None

            # Measure LLM latency
            llm_start = time.time()
            try:
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
            except Exception as e:
                self._error_counter.inc()
                logger.exception("LLM stream failed")
                yield ErrorEvent(error=e, recoverable=False)
                return
            finally:
                self._llm_latency_hist.observe(time.time() - llm_start)

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
                # Measure tool execution latency
                self._tool_counter.inc()
                tool_start = time.time()
                result = await self._execute_tool(current_tool_use)
                self._tool_latency_hist.observe(time.time() - tool_start)
                if result.is_error:
                    self._tool_error_counter.inc()

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

    def reconfigure(
        self,
        system_prompt: str | None = None,
        tool_registry: ToolRegistry | None = None,
        max_turns: int | None = None,
        permission_checker: PermissionChecker | None = None,
    ) -> None:
        """Reconfigure the query engine with new settings."""
        if system_prompt is not None:
            self.system_prompt = system_prompt
        if tool_registry is not None:
            self.tool_registry = tool_registry
        if max_turns is not None:
            self.max_turns = max_turns
        if permission_checker is not None:
            self.permission_checker = permission_checker

        self.messages = [
            ConversationMessage.from_system_text(self.system_prompt)
        ]
        self._turn_count = 0

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
