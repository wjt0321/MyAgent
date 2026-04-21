"""Glob tool for MyAgent."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


class GlobInput(BaseModel):
    pattern: str = Field(description="The glob pattern to match files")


class Glob(BaseTool):
    name = "Glob"
    description = "Find files matching a glob pattern."
    input_model = GlobInput

    async def execute(self, arguments: GlobInput, context: ToolExecutionContext) -> ToolResult:
        try:
            pattern = arguments.pattern
            matches = sorted(context.cwd.glob(pattern))
            if not matches:
                return ToolResult(output="No files matched the pattern.")

            lines = [str(m.relative_to(context.cwd)) for m in matches]
            return ToolResult(output="\n".join(lines))
        except Exception as e:
            return ToolResult(output=f"Error: {e}", is_error=True)

    def is_read_only(self, arguments: BaseModel) -> bool:
        return True
