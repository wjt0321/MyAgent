"""Git tool for MyAgent."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


class GitInput(BaseModel):
    command: str = Field(
        description="Git subcommand to execute",
        json_schema_extra={"enum": ["status", "diff", "log", "add", "commit", "push", "branch", "checkout"]},
    )
    args: str = Field(default="", description="Additional arguments for the git command")
    path: str = Field(default=".", description="Working directory for git command")


class Git(BaseTool):
    name = "Git"
    description = """Execute git operations: status, diff, log, add, commit, push, branch, checkout.

Commands:
- status: Show working tree status
- diff: Show changes between commits, commit and working tree, etc.
- log: Show commit logs (limit optional)
- add: Add file contents to the index
- commit: Record changes to the repository (requires message)
- push: Update remote refs along with associated objects
- branch: List, create, or delete branches
- checkout: Switch branches or restore working tree files
"""
    input_model = GitInput

    def is_read_only(self, arguments: GitInput) -> bool:
        return arguments.command in ("status", "diff", "log", "branch")

    async def execute(self, arguments: GitInput, context: ToolExecutionContext) -> ToolResult:
        work_dir = Path(arguments.path).resolve()
        if not work_dir.exists():
            return ToolResult(
                output=f"Error: Path does not exist: {work_dir}",
                is_error=True,
            )

        cmd = ["git", arguments.command]
        if arguments.args:
            cmd.extend(arguments.args.split())

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(work_dir),
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=30
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
            return ToolResult(
                output="Error: Git command timed out after 30 seconds.",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Error executing git command: {e}",
                is_error=True,
            )
