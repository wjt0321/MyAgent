"""Tool registry for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.tools.base import BaseTool


class ToolRegistry:
    """Map tool names to implementations."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """Return a registered tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def to_api_schema(self) -> list[dict[str, Any]]:
        """Return all tool schemas in API format."""
        return [tool.to_api_schema() for tool in self._tools.values()]

    @classmethod
    def with_core_tools(cls) -> "ToolRegistry":
        """Create a registry with all core tools registered."""
        from myagent.tools.bash import Bash
        from myagent.tools.read import Read
        from myagent.tools.write import Write
        from myagent.tools.edit import Edit
        from myagent.tools.glob import Glob
        from myagent.tools.grep import Grep
        from myagent.tools.web_search import WebSearch
        from myagent.tools.web_fetch import WebFetch
        from myagent.tools.git import Git

        registry = cls()
        registry.register(Bash())
        registry.register(Read())
        registry.register(Write())
        registry.register(Edit())
        registry.register(Glob())
        registry.register(Grep())
        registry.register(WebSearch())
        registry.register(WebFetch())
        registry.register(Git())
        return registry
