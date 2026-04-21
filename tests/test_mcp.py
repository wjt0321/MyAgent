"""Tests for MCP support."""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from myagent.mcp.client import MCPClient, MCPClientManager
from myagent.mcp.config import MCPStdioConfig
from myagent.mcp.types import MCPToolInfo


class TestMCPStdioConfig:
    def test_config_creation(self):
        config = MCPStdioConfig(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        )
        assert config.name == "filesystem"
        assert config.command == "npx"
        assert config.args == ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        assert config.transport == "stdio"

    def test_config_env(self):
        config = MCPStdioConfig(
            name="test",
            command="python",
            args=["server.py"],
            env={"API_KEY": "secret"},
        )
        assert config.env == {"API_KEY": "secret"}


class TestMCPToolInfo:
    def test_tool_info_creation(self):
        tool = MCPToolInfo(
            name="read_file",
            description="Read a file",
            input_schema={"type": "object", "properties": {}},
            server="filesystem",
        )
        assert tool.name == "read_file"
        assert tool.server == "filesystem"


class TestMCPClientManager:
    def test_manager_creation(self):
        configs = {
            "fs": MCPStdioConfig(name="fs", command="npx", args=["server"]),
        }
        manager = MCPClientManager(configs)
        assert "fs" in manager._configs

    def test_list_servers(self):
        configs = {
            "fs": MCPStdioConfig(name="fs", command="npx", args=["server"]),
            "db": MCPStdioConfig(name="db", command="python", args=["db.py"]),
        }
        manager = MCPClientManager(configs)
        servers = manager.list_servers()
        assert len(servers) == 2
        assert "fs" in servers
        assert "db" in servers

    def test_get_tools_empty(self):
        configs = {}
        manager = MCPClientManager(configs)
        tools = manager.get_tools()
        assert tools == []

    @pytest.mark.asyncio
    async def test_manager_connect_all(self):
        configs = {
            "fs": MCPStdioConfig(name="fs", command="npx", args=["server"]),
        }
        manager = MCPClientManager(configs)

        mock_tools = [
            MCPToolInfo(name="read_file", description="Read a file", input_schema={}, server="fs")
        ]

        manager._clients["fs"].connected = True
        manager._clients["fs"]._tools = mock_tools

        tools = manager.get_tools()
        assert len(tools) == 1
        assert tools[0].name == "read_file"

    @pytest.mark.asyncio
    async def test_manager_call_tool(self):
        configs = {
            "fs": MCPStdioConfig(name="fs", command="npx", args=["server"]),
        }
        manager = MCPClientManager(configs)

        with patch.object(manager._clients["fs"], "call_tool", return_value="file content") as mock_call:
            result = await manager.call_tool("fs", "read_file", {"path": "/tmp/test.txt"})

        assert result == "file content"
        mock_call.assert_called_once_with("read_file", {"path": "/tmp/test.txt"})

    @pytest.mark.asyncio
    async def test_manager_call_tool_unknown_server(self):
        configs = {}
        manager = MCPClientManager(configs)

        with pytest.raises(ValueError, match="Unknown MCP server"):
            await manager.call_tool("unknown", "tool", {})

    @pytest.mark.asyncio
    async def test_manager_disconnect_all(self):
        configs = {
            "fs": MCPStdioConfig(name="fs", command="npx", args=["server"]),
        }
        manager = MCPClientManager(configs)

        with patch.object(manager._clients["fs"], "disconnect") as mock_disconnect:
            await manager.disconnect_all()

        mock_disconnect.assert_called_once()


class TestMCPClient:
    @pytest.mark.asyncio
    async def test_client_creation(self):
        config = MCPStdioConfig(name="fs", command="npx", args=["server"])
        client = MCPClient(config)
        assert client.config == config
        assert client.connected is False

    @pytest.mark.asyncio
    async def test_client_connect_mocked(self):
        config = MCPStdioConfig(name="fs", command="npx", args=["server"])
        client = MCPClient(config)

        mock_proc = MagicMock()
        mock_proc.stdin = AsyncMock()
        mock_proc.stdout = AsyncMock()
        mock_proc.terminate = MagicMock()
        mock_proc.wait = AsyncMock(return_value=0)

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            await client.connect()

        assert client.connected is True

    @pytest.mark.asyncio
    async def test_client_list_tools_mocked(self):
        config = MCPStdioConfig(name="fs", command="npx", args=["server"])
        client = MCPClient(config)
        client.connected = True
        client._tools = [
            MCPToolInfo(name="read", description="Read", input_schema={}, server="fs"),
            MCPToolInfo(name="write", description="Write", input_schema={}, server="fs"),
        ]

        tools = await client.list_tools()
        assert len(tools) == 2
        assert tools[0].name == "read"

    @pytest.mark.asyncio
    async def test_client_disconnect(self):
        config = MCPStdioConfig(name="fs", command="npx", args=["server"])
        client = MCPClient(config)
        client.connected = True

        mock_proc = MagicMock()
        mock_proc.terminate = MagicMock()
        mock_proc.wait = AsyncMock(return_value=0)
        client._process = mock_proc

        await client.disconnect()

        assert client.connected is False
        mock_proc.terminate.assert_called_once()
