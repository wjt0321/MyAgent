"""MCP configuration types for MyAgent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MCPStdioConfig(BaseModel):
    """Configuration for an MCP server using stdio transport."""

    name: str = Field(description="Server identifier")
    command: str = Field(description="Command to execute")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict[str, str] | None = Field(default=None, description="Environment variables")
    cwd: str | None = Field(default=None, description="Working directory")
    transport: str = Field(default="stdio", description="Transport type")


class MCPHttpConfig(BaseModel):
    """Configuration for an MCP server using HTTP/SSE transport."""

    name: str = Field(description="Server identifier")
    url: str = Field(description="Server URL")
    headers: dict[str, str] | None = Field(default=None, description="HTTP headers")
    transport: str = Field(default="http", description="Transport type")
