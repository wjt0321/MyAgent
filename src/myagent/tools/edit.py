"""Edit tool for MyAgent."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


class EditInput(BaseModel):
    path: str = Field(description="The path of the file to edit")
    old_string: str = Field(description="The string to replace")
    new_string: str = Field(description="The replacement string")


class Edit(BaseTool):
    name = "Edit"
    description = "Edit a file by replacing a string with another string."
    input_model = EditInput

    async def execute(self, arguments: EditInput, context: ToolExecutionContext) -> ToolResult:
        target = Path(arguments.path)
        if not target.is_absolute():
            target = context.cwd / target

        if not target.exists():
            return ToolResult(output=f"Error: File '{arguments.path}' does not exist.", is_error=True)

        try:
            content = target.read_text(encoding="utf-8")

            if arguments.old_string not in content:
                return ToolResult(
                    output=f"Error: The specified old_string was not found in '{arguments.path}'.",
                    is_error=True,
                )

            new_content = content.replace(arguments.old_string, arguments.new_string, 1)
            target.write_text(new_content, encoding="utf-8")

            return ToolResult(output=f"File edited successfully: {arguments.path}")
        except Exception as e:
            return ToolResult(output=f"Error editing file: {e}", is_error=True)
