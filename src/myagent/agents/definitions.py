"""Agent definition models for MyAgent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentDefinition(BaseModel):
    """Defines an agent's behavior, capabilities, and configuration."""

    name: str | None = Field(default=None, description="Agent identifier")
    description: str | None = Field(default=None, description="Short description")
    system_prompt: str | None = Field(default=None, description="System prompt text")
    tools: list[str] | None = Field(default=None, description="Allowed tool names")
    disallowed_tools: list[str] | None = Field(default=None, description="Disallowed tool names")
    model: str | None = Field(default=None, description="LLM model identifier")
    effort: str | int | None = Field(default=None, description="Effort level")
    permission_mode: str | None = Field(default=None, description="Permission mode")
    max_turns: int | None = Field(default=None, description="Maximum conversation turns")
    skills: list[str] = Field(default_factory=list, description="Agent skills")
    mcp_servers: list[str | dict] | None = Field(default=None, description="MCP server configs")
    hooks: dict[str, object] | None = Field(default=None, description="Hook configurations")
    color: str | None = Field(default=None, description="Display color")
    background: bool = Field(default=False, description="Run in background")
    initial_prompt: str | None = Field(default=None, description="Initial prompt")
    memory: str | None = Field(default=None, description="Memory scope")
    isolation: str | None = Field(default=None, description="Isolation mode")
    critical_system_reminder: str | None = Field(default=None, description="Critical reminder")
