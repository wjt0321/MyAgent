"""WebFetch tool for MyAgent."""

from __future__ import annotations

import ipaddress
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


BLOCKED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
]

BLOCKED_PREFIXES = [
    "10.",
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",
    "192.168.",
    "169.254.",
]


def is_safe_url(url: str) -> bool:
    """Check if URL is safe to fetch (SSRF protection)."""
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    # Check blocked hosts
    for blocked in BLOCKED_HOSTS:
        if hostname.lower() == blocked.lower():
            return False

    # Check blocked prefixes
    for prefix in BLOCKED_PREFIXES:
        if hostname.startswith(prefix):
            return False

    # Check IP addresses
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        pass

    return True


class WebFetchInput(BaseModel):
    url: str = Field(description="The URL to fetch")
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Optional custom HTTP headers",
    )


class WebFetch(BaseTool):
    name = "WebFetch"
    description = (
        "Fetch the content of a web page. "
        "Returns the HTML/text content of the specified URL."
    )
    input_model = WebFetchInput

    async def execute(
        self, arguments: WebFetchInput, context: ToolExecutionContext
    ) -> ToolResult:
        if not is_safe_url(arguments.url):
            return ToolResult(
                output="Error: Access to internal/private addresses is blocked for security.",
                is_error=True,
            )

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(arguments.url, headers=arguments.headers)

            if response.status_code >= 400:
                return ToolResult(
                    output=f"HTTP Error {response.status_code}: {response.text[:500]}",
                    is_error=True,
                )

            content_type = response.headers.get("content-type", "")
            text = response.text

            if len(text) > 100_000:
                text = text[:100_000] + "\n... [content truncated]"

            output = f"URL: {arguments.url}\nStatus: {response.status_code}\nContent-Type: {content_type}\n\n{text}"
            return ToolResult(output=output)

        except httpx.TimeoutException:
            return ToolResult(
                output=f"Request timeout fetching {arguments.url}",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Error fetching {arguments.url}: {e}",
                is_error=True,
            )

    def is_read_only(self, arguments: BaseModel) -> bool:
        return True
