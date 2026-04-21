"""WebSearch tool for MyAgent."""

from __future__ import annotations

import urllib.parse
from typing import Any

import httpx
from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


class WebSearchInput(BaseModel):
    query: str = Field(description="The search query")
    num_results: int = Field(
        default=5,
        description="Number of results to return (max 10)",
    )


class WebSearch(BaseTool):
    name = "WebSearch"
    description = (
        "Search the web for information. "
        "Returns a list of search results with titles, URLs, and snippets."
    )
    input_model = WebSearchInput

    async def execute(
        self, arguments: WebSearchInput, context: ToolExecutionContext
    ) -> ToolResult:
        query = arguments.query.strip()
        if not query:
            return ToolResult(output="Error: Search query cannot be empty.", is_error=True)

        num_results = min(max(arguments.num_results, 1), 10)

        try:
            search_url = self._build_search_url(query)

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(
                    search_url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.0"
                        ),
                    },
                )

            if response.status_code >= 400:
                return ToolResult(
                    output=f"HTTP Error {response.status_code} from search engine",
                    is_error=True,
                )

            results = self._parse_results(response.text, num_results)

            if not results:
                return ToolResult(output=f'No results found for "{query}".')

            lines = [f'Search results for "{query}":\n']
            for i, result in enumerate(results, 1):
                lines.append(f"{i}. {result['title']}")
                lines.append(f"   URL: {result['url']}")
                lines.append(f"   {result['snippet']}\n")

            return ToolResult(output="\n".join(lines))

        except httpx.TimeoutException:
            return ToolResult(
                output=f"Search request timeout for query: {query}",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Search error: {e}",
                is_error=True,
            )

    def _build_search_url(self, query: str) -> str:
        encoded = urllib.parse.quote(query)
        return f"https://www.google.com/search?q={encoded}&hl=en"

    def _parse_results(self, html: str, limit: int) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []

        try:
            from html.parser import HTMLParser

            class SimpleGoogleParser(HTMLParser):
                def __init__(self) -> None:
                    super().__init__()
                    self.results: list[dict[str, str]] = []
                    self._current: dict[str, str] = {}
                    self._in_result = False
                    self._in_title = False
                    self._in_snippet = False
                    self._data_buffer = ""
                    self._href = ""

                def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                    attr_dict = {k: v or "" for k, v in attrs}

                    if tag == "div" and "g" in attr_dict.get("class", "").split():
                        self._in_result = True
                        self._current = {}

                    if self._in_result and tag == "a" and "href" in attr_dict:
                        href = attr_dict["href"]
                        if href.startswith("http") and "google.com" not in href:
                            self._href = href
                            self._in_title = True

                    if self._in_result and tag == "div":
                        classes = attr_dict.get("class", "")
                        if "VwiC3b" in classes or "s3v94d" in classes:
                            self._in_snippet = True

                def handle_data(self, data: str) -> None:
                    if self._in_title or self._in_snippet:
                        self._data_buffer += data

                def handle_endtag(self, tag: str) -> None:
                    if self._in_title and tag == "a":
                        self._current["title"] = self._data_buffer.strip()
                        self._current["url"] = self._href
                        self._in_title = False
                        self._data_buffer = ""

                    if self._in_snippet and tag == "div":
                        self._current["snippet"] = self._data_buffer.strip()
                        self._in_snippet = False
                        self._data_buffer = ""
                        if self._current.get("title") and self._current.get("url"):
                            self.results.append(self._current.copy())
                        self._in_result = False

            parser = SimpleGoogleParser()
            parser.feed(html)
            results = parser.results[:limit]

        except Exception:
            pass

        if not results:
            results = self._fallback_parse(html, limit)

        return results

    def _fallback_parse(self, html: str, limit: int) -> list[dict[str, str]]:
        import re

        results: list[dict[str, str]] = []

        link_pattern = re.compile(
            r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL
        )
        matches = link_pattern.findall(html)

        for href, title_html in matches[:limit * 3]:
            if "google.com" in href or href.startswith("https://www.google.com"):
                continue

            title = re.sub(r'<[^>]+>', '', title_html).strip()
            if title and len(title) > 3:
                results.append({
                    "title": title,
                    "url": href,
                    "snippet": "",
                })

            if len(results) >= limit:
                break

        return results

    def is_read_only(self, arguments: BaseModel) -> bool:
        return True
