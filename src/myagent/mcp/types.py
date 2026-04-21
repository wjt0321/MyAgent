"""MCP types for MyAgent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MCPToolInfo(BaseModel):
    """Information about an MCP tool."""

    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    input_schema: dict = Field(description="JSON schema for tool input")
    server: str = Field(description="Name of the MCP server providing this tool")


class MCPResourceInfo(BaseModel):
    """Information about an MCP resource."""

    uri: str = Field(description="Resource URI")
    name: str = Field(description="Resource name")
    mime_type: str | None = Field(default=None, description="MIME type")
    server: str = Field(description="Name of the MCP server providing this resource")


class MCPConnectionStatus(BaseModel):
    """Status of an MCP server connection."""

    name: str = Field(description="Server name")
    state: str = Field(description="Connection state: pending, connected, failed")
    transport: str = Field(default="stdio", description="Transport type")
    detail: str | None = Field(default=None, description="Status detail or error message")
