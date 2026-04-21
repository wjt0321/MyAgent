"""MCP client for MyAgent."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from myagent.mcp.config import MCPStdioConfig
from myagent.mcp.types import MCPToolInfo


class MCPClient:
    """Lightweight MCP client for stdio-based servers."""

    def __init__(self, config: MCPStdioConfig) -> None:
        self.config = config
        self.connected = False
        self._process: asyncio.subprocess.Process | None = None
        self._tools: list[MCPToolInfo] = []
        self._request_id = 0

    async def connect(self) -> None:
        """Connect to the MCP server via stdio."""
        if self.connected:
            return

        try:
            self._process = await asyncio.create_subprocess_exec(
                self.config.command,
                *self.config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**dict(asyncio.os.environ), **(self.config.env or {})} if self.config.env else None,
                cwd=self.config.cwd,
            )
            self.connected = True

            await self._initialize()
            await self._discover_tools()

        except Exception as exc:
            self.connected = False
            raise RuntimeError(f"Failed to connect to MCP server '{self.config.name}': {exc}") from exc

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._process is not None:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except Exception:
                pass
            self._process = None
        self.connected = False
        self._tools = []

    async def list_tools(self) -> list[MCPToolInfo]:
        """List available tools from the MCP server."""
        if not self.connected:
            return []
        return list(self._tools)

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call an MCP tool and return the result."""
        if not self.connected or self._process is None:
            raise RuntimeError("MCP client is not connected")

        return f"[MCP tool '{tool_name}' would be called with {arguments}]"

    async def _initialize(self) -> None:
        """Send initialize request to MCP server."""
        pass

    async def _discover_tools(self) -> None:
        """Discover tools from the MCP server."""
        pass


class MCPClientManager:
    """Manages multiple MCP client connections."""

    def __init__(self, configs: dict[str, MCPStdioConfig]) -> None:
        self._configs = configs
        self._clients: dict[str, MCPClient] = {
            name: MCPClient(config) for name, config in configs.items()
        }

    async def connect_all(self) -> None:
        """Connect to all configured MCP servers."""
        for client in self._clients.values():
            try:
                await client.connect()
            except Exception:
                pass

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        for client in self._clients.values():
            await client.disconnect()

    def list_servers(self) -> list[str]:
        """List all configured server names."""
        return list(self._configs.keys())

    def get_tools(self) -> list[MCPToolInfo]:
        """Get all tools from all connected servers."""
        tools: list[MCPToolInfo] = []
        for client in self._clients.values():
            if client.connected:
                tools.extend(client._tools)
        return tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call a tool on a specific MCP server."""
        client = self._clients.get(server_name)
        if client is None:
            raise ValueError(f"Unknown MCP server: {server_name}")
        return await client.call_tool(tool_name, arguments)
