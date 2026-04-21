"""Read tool for MyAgent."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


class ReadInput(BaseModel):
    path: str = Field(description="The path of the file to read")


class Read(BaseTool):
    name = "Read"
    description = "Read the contents of a file."
    input_model = ReadInput

    async def execute(self, arguments: ReadInput, context: ToolExecutionContext) -> ToolResult:
        target = Path(arguments.path)
        if not target.is_absolute():
            target = context.cwd / target

        if not target.exists():
            return ToolResult(output=f"Error: File '{arguments.path}' does not exist.", is_error=True)

        if not target.is_file():
            return ToolResult(output=f"Error: '{arguments.path}' is not a file.", is_error=True)

        try:
            content = target.read_text(encoding="utf-8")
            return ToolResult(output=content)
        except Exception as e:
            return ToolResult(output=f"Error reading file: {e}", is_error=True)

    def is_read_only(self, arguments: BaseModel) -> bool:
        return True
