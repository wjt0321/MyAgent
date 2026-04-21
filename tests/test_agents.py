"""Tests for myagent agents."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from myagent.agents.definitions import AgentDefinition
from myagent.agents.loader import AgentLoader


class TestAgentDefinition:
    def test_agent_definition_creation(self):
        agent = AgentDefinition(
            name="test-agent",
            description="A test agent",
            system_prompt="You are a test agent.",
        )
        assert agent.name == "test-agent"
        assert agent.description == "A test agent"
        assert agent.system_prompt == "You are a test agent."

    def test_agent_definition_defaults(self):
        agent = AgentDefinition(name="minimal", description="Minimal agent")
        assert agent.tools is None
        assert agent.model is None
        assert agent.max_turns is None
        assert agent.permission_mode is None

    def test_agent_definition_tools_list(self):
        agent = AgentDefinition(
            name="coder",
            description="Coding agent",
            tools=["Read", "Write", "Edit"],
        )
        assert agent.tools == ["Read", "Write", "Edit"]

    def test_agent_definition_empty_name(self):
        agent = AgentDefinition(name="", description="Empty name allowed for now")
        assert agent.name == ""


class TestAgentLoader:
    def test_parse_frontmatter(self):
        content = """---
name: explore
description: Code exploration agent
tools: [Read, Glob, Grep]
model: sonnet
max_turns: 20
---

You are a code exploration expert.
"""
        agent = AgentLoader.parse_agent_definition(content)
        assert agent.name == "explore"
        assert agent.description == "Code exploration agent"
        assert agent.tools == ["Read", "Glob", "Grep"]
        assert agent.model == "sonnet"
        assert agent.max_turns == 20
        assert agent.system_prompt == "You are a code exploration expert."

    def test_parse_without_frontmatter(self):
        content = "Just a plain description."
        agent = AgentLoader.parse_agent_definition(content)
        assert agent.name is None
        assert agent.description is None
        assert agent.system_prompt == "Just a plain description."

    def test_parse_frontmatter_only(self):
        content = """---
name: test
description: test agent
---"""
        agent = AgentLoader.parse_agent_definition(content)
        assert agent.name == "test"
        assert agent.system_prompt == ""

    def test_load_from_directory(self, tmp_path: Path):
        agent_dir = tmp_path / "agents"
        agent_dir.mkdir()

        (agent_dir / "general.md").write_text(
            "---\nname: general\ndescription: General purpose agent\n---\n\nYou are helpful.",
            encoding="utf-8",
        )
        (agent_dir / "explore.md").write_text(
            "---\nname: explore\ndescription: Explorer\n---\n\nYou explore.",
            encoding="utf-8",
        )

        loader = AgentLoader(search_paths=[agent_dir])
        agents = loader.load_all()

        assert len(agents) == 2
        assert "general" in agents
        assert "explore" in agents
        assert agents["general"].description == "General purpose agent"

    def test_load_builtin_agents(self):
        loader = AgentLoader()
        agents = loader.load_builtin_agents()

        assert "general" in agents
        assert "explore" in agents
        assert "plan" in agents
        assert "worker" in agents

    def test_agent_with_complex_frontmatter(self):
        content = """---
name: advanced
description: Advanced agent
tools:
  - Read
  - Write
  - Bash
disallowed_tools:
  - Edit
model: gpt-4o
permission_mode: dontAsk
max_turns: 50
memory: project
color: cyan
---

Advanced system prompt here.
With multiple lines.
"""
        agent = AgentLoader.parse_agent_definition(content)
        assert agent.name == "advanced"
        assert agent.tools == ["Read", "Write", "Bash"]
        assert agent.disallowed_tools == ["Edit"]
        assert agent.model == "gpt-4o"
        assert agent.permission_mode == "dontAsk"
        assert agent.max_turns == 50
        assert agent.memory == "project"
        assert agent.color == "cyan"
        assert "Advanced system prompt here." in agent.system_prompt
