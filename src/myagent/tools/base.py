"""Tool abstractions for MyAgent."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


@dataclass
class ToolExecutionContext:
    """Shared execution context for tool invocations."""

    cwd: Path
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """Normalized tool execution result."""

    output: str
    is_error: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """Base class for all MyAgent tools.

    Features:
    - Default timeout support
    - Read-only checking
    - Standardized execution
    """

    name: str
    description: str
    input_model: type[BaseModel]
    default_timeout: int = 30  # Default timeout in seconds

    @abstractmethod
    async def _execute_impl(
        self, arguments: BaseModel, context: ToolExecutionContext
    ) -> ToolResult:
        """Implementation of tool execution (without timeout wrapper)."""

    async def execute(
        self, arguments: BaseModel, context: ToolExecutionContext
    ) -> ToolResult:
        """Execute the tool with automatic timeout handling.

        Will use default_timeout unless overridden by tool's input model.
        """
        # Try to get timeout from arguments
        timeout = self.default_timeout
        try:
            if hasattr(arguments, "timeout"):
                timeout = getattr(arguments, "timeout")
        except Exception:
            pass

        try:
            return await asyncio.wait_for(
                self._execute_impl(arguments, context),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return ToolResult(
                output=f"Error: Tool '{self.name}' timed out after {timeout} seconds.",
                is_error=True,
                metadata={"timeout": timeout}
            )
        except Exception as e:
            return ToolResult(
                output=f"Error executing '{self.name}': {e}",
                is_error=True,
                metadata={"error": str(e)}
            )

    def is_read_only(self, arguments: BaseModel) -> bool:
        """Return whether the invocation is read-only."""
        del arguments
        return False

    def to_api_schema(self) -> dict[str, Any]:
        """Return the tool schema expected by the LLM API."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_model.model_json_schema(),
        }
