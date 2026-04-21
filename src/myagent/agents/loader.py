"""Agent loader for MyAgent."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from myagent.agents.definitions import AgentDefinition


class AgentLoader:
    """Load agent definitions from Markdown + YAML frontmatter files."""

    FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)

    def __init__(self, search_paths: list[Path] | None = None) -> None:
        self.search_paths = search_paths or []

    @classmethod
    def parse_agent_definition(cls, content: str) -> AgentDefinition:
        """Parse an agent definition from Markdown + YAML frontmatter."""
        match = cls.FRONTMATTER_RE.match(content)

        if match:
            frontmatter_text = match.group(1)
            body = match.group(2)
            try:
                frontmatter = yaml.safe_load(frontmatter_text) or {}
            except yaml.YAMLError:
                frontmatter = {}
        else:
            frontmatter = {}
            body = content

        data: dict[str, Any] = dict(frontmatter)
        data["system_prompt"] = body.strip()

        return AgentDefinition.model_validate(data)

    def load_all(self) -> dict[str, AgentDefinition]:
        """Load all agent definitions from search paths."""
        agents: dict[str, AgentDefinition] = {}

        for path in self.search_paths:
            if not path.exists():
                continue
            for file_path in path.glob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    agent = self.parse_agent_definition(content)
                    if agent.name:
                        agents[agent.name] = agent
                except Exception:
                    continue

        return agents

    def load_builtin_agents(self) -> dict[str, AgentDefinition]:
        """Load built-in agent definitions."""
        builtin_dir = Path(__file__).parent / "builtin"
        if not builtin_dir.exists():
            return {}

        self.search_paths = [builtin_dir]
        return self.load_all()
