"""Write tool for MyAgent."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


class WriteInput(BaseModel):
    path: str = Field(description="The path of the file to write")
    content: str = Field(description="The content to write to the file")


class Write(BaseTool):
    name = "Write"
    description = "Write content to a file. Creates the file if it does not exist, overwrites if it does."
    input_model = WriteInput

    async def execute(self, arguments: WriteInput, context: ToolExecutionContext) -> ToolResult:
        target = Path(arguments.path)
        if not target.is_absolute():
            target = context.cwd / target

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(arguments.content, encoding="utf-8")
            return ToolResult(output=f"File written successfully: {arguments.path}")
        except Exception as e:
            return ToolResult(output=f"Error writing file: {e}", is_error=True)
