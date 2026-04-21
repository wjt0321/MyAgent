"""Tool abstractions for MyAgent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel


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
    """Base class for all MyAgent tools."""

    name: str
    description: str
    input_model: type[BaseModel]

    @abstractmethod
    async def execute(
        self, arguments: BaseModel, context: ToolExecutionContext
    ) -> ToolResult:
        """Execute the tool."""

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
