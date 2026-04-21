"""WebFetch tool for MyAgent."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


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
