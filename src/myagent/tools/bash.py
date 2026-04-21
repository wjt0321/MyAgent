"""Bash tool for MyAgent."""

from __future__ import annotations

import asyncio
import shlex

from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


class BashInput(BaseModel):
    command: str = Field(description="The bash command to execute")
    timeout: int = Field(default=30, description="Timeout in seconds")


class Bash(BaseTool):
    name = "Bash"
    description = "Execute a bash command."
    input_model = BashInput

    async def execute(self, arguments: BashInput, context: ToolExecutionContext) -> ToolResult:
        try:
            process = await asyncio.create_subprocess_shell(
                arguments.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(context.cwd),
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=arguments.timeout
            )

            output = stdout.decode("utf-8", errors="replace")
            if stderr:
                err_text = stderr.decode("utf-8", errors="replace")
                if output:
                    output += f"\n[stderr]\n{err_text}"
                else:
                    output = err_text

            if process.returncode != 0:
                return ToolResult(
                    output=f"Exit code {process.returncode}: {output}",
                    is_error=True,
                )

            return ToolResult(output=output or "")
        except asyncio.TimeoutError:
            process.kill()
            return ToolResult(output="Error: Command timed out.", is_error=True)
        except Exception as e:
            return ToolResult(output=f"Error executing command: {e}", is_error=True)
