"""Tests for Web tools (WebFetch, WebSearch)."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from myagent.tools.base import ToolExecutionContext, ToolResult
from myagent.tools.web_fetch import WebFetch, WebFetchInput
from myagent.tools.web_search import WebSearch, WebSearchInput


class TestWebFetchTool:
    def test_web_fetch_creation(self):
        tool = WebFetch()
        assert tool.name == "WebFetch"
        assert "fetch" in tool.description.lower()

    def test_web_fetch_is_read_only(self):
        tool = WebFetch()
        assert tool.is_read_only(None) is True

    @pytest.mark.asyncio
    async def test_web_fetch_success(self):
        tool = WebFetch()
        ctx = ToolExecutionContext(cwd=Path("."))

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Hello World</body></html>"
        mock_response.headers = {"content-type": "text/html"}

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await tool.execute(WebFetchInput(url="https://example.com"), ctx)

        assert result.is_error is False
        assert "Hello World" in result.output

    @pytest.mark.asyncio
    async def test_web_fetch_with_custom_headers(self):
        tool = WebFetch()
        ctx = ToolExecutionContext(cwd=Path("."))

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "API response"
        mock_response.headers = {"content-type": "application/json"}

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await tool.execute(
                WebFetchInput(url="https://api.example.com/data", headers={"Authorization": "Bearer token"}),
                ctx,
            )

        assert result.is_error is False
        assert "API response" in result.output

    @pytest.mark.asyncio
    async def test_web_fetch_http_error(self):
        tool = WebFetch()
        ctx = ToolExecutionContext(cwd=Path("."))

        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.headers = {}

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await tool.execute(WebFetchInput(url="https://example.com/notfound"), ctx)

        assert result.is_error is True
        assert "404" in result.output

    @pytest.mark.asyncio
    async def test_web_fetch_network_error(self):
        tool = WebFetch()
        ctx = ToolExecutionContext(cwd=Path("."))

        with patch("httpx.AsyncClient.get", side_effect=Exception("Connection refused")):
            result = await tool.execute(WebFetchInput(url="https://example.com"), ctx)

        assert result.is_error is True
        assert "Connection refused" in result.output

    @pytest.mark.asyncio
    async def test_web_fetch_timeout(self):
        tool = WebFetch()
        ctx = ToolExecutionContext(cwd=Path("."))

        with patch("httpx.AsyncClient.get", side_effect=Exception("Request timeout")):
            result = await tool.execute(WebFetchInput(url="https://slow.example.com"), ctx)

        assert result.is_error is True
        assert "timeout" in result.output.lower()


class TestWebSearchTool:
    def test_web_search_creation(self):
        tool = WebSearch()
        assert tool.name == "WebSearch"
        assert "search" in tool.description.lower()

    def test_web_search_is_read_only(self):
        tool = WebSearch()
        assert tool.is_read_only(None) is True

    @pytest.mark.asyncio
    async def test_web_search_success(self):
        tool = WebSearch()
        ctx = ToolExecutionContext(cwd=Path("."))

        mock_html = """
        <html>
        <body>
            <div class="g">
                <h3><a href="https://result1.com">Result 1 Title</a></h3>
                <div class="VwiC3b">Result 1 snippet text here</div>
            </div>
            <div class="g">
                <h3><a href="https://result2.com">Result 2 Title</a></h3>
                <div class="VwiC3b">Result 2 snippet text here</div>
            </div>
        </body>
        </html>
        """

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.headers = {"content-type": "text/html"}

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await tool.execute(WebSearchInput(query="python asyncio"), ctx)

        assert result.is_error is False
        assert "Result 1 Title" in result.output
        assert "result1.com" in result.output
        assert "Result 2 Title" in result.output

    @pytest.mark.asyncio
    async def test_web_search_no_results(self):
        tool = WebSearch()
        ctx = ToolExecutionContext(cwd=Path("."))

        mock_html = "<html><body><div class=""g""></div></body></html>"

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.headers = {}

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await tool.execute(WebSearchInput(query="xyznonexistent12345"), ctx)

        assert result.is_error is False
        assert "No results" in result.output or "0 results" in result.output

    @pytest.mark.asyncio
    async def test_web_search_http_error(self):
        tool = WebSearch()
        ctx = ToolExecutionContext(cwd=Path("."))

        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limited"
        mock_response.headers = {}

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await tool.execute(WebSearchInput(query="test"), ctx)

        assert result.is_error is True
        assert "429" in result.output

    @pytest.mark.asyncio
    async def test_web_search_network_error(self):
        tool = WebSearch()
        ctx = ToolExecutionContext(cwd=Path("."))

        with patch("httpx.AsyncClient.get", side_effect=Exception("Network error")):
            result = await tool.execute(WebSearchInput(query="test"), ctx)

        assert result.is_error is True
        assert "Network error" in result.output
