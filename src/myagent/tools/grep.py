"""Grep tool for MyAgent."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


class GrepInput(BaseModel):
    pattern: str = Field(description="The regex pattern to search for")
    glob: str | None = Field(default=None, description="Optional glob pattern to filter files")


class Grep(BaseTool):
    name = "Grep"
    description = "Search for a regex pattern in files."
    input_model = GrepInput

    async def execute(self, arguments: GrepInput, context: ToolExecutionContext) -> ToolResult:
        try:
            regex = re.compile(arguments.pattern)
            results: list[str] = []

            for file_path in context.cwd.rglob("*"):
                if not file_path.is_file():
                    continue
                if arguments.glob and not fnmatch.fnmatch(file_path.name, arguments.glob):
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                    for i, line in enumerate(content.splitlines(), start=1):
                        if regex.search(line):
                            rel = file_path.relative_to(context.cwd)
                            results.append(f"{rel}:{i}: {line.strip()}")
                except Exception:
                    continue

            if not results:
                return ToolResult(output="No matches found.")

            return ToolResult(output="\n".join(results))
        except re.error as e:
            return ToolResult(output=f"Invalid regex pattern: {e}", is_error=True)
        except Exception as e:
            return ToolResult(output=f"Error: {e}", is_error=True)

    def is_read_only(self, arguments: BaseModel) -> bool:
        return True
