"""Configuration settings for MyAgent."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    default: str = "anthropic/claude-sonnet-4"
    fallback: str | None = None


class ProviderConfig(BaseModel):
    api_key: str | None = None


class ContextConfig(BaseModel):
    auto_compact_threshold: float = 0.8
    max_turns: int = 50


class MemoryConfig(BaseModel):
    enabled: bool = True
    scope: str = "project"


class PluginConfig(BaseModel):
    enabled: list[str] = Field(default_factory=list)


class MCPConfig(BaseModel):
    servers: dict[str, dict[str, Any]] = Field(default_factory=dict)


class GatewayConfig(BaseModel):
    discord: dict[str, str] | None = None
    slack: dict[str, str] | None = None


class LoggingConfig(BaseModel):
    level: str = "info"
    trajectory: bool = True
    trajectory_path: str = "~/.myagent/trajectories/"


class Settings(BaseModel):
    """MyAgent configuration settings."""

    model: ModelConfig = Field(default_factory=ModelConfig)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    context: ContextConfig = Field(default_factory=ContextConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    plugins: PluginConfig = Field(default_factory=PluginConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    github_token: str | None = Field(default=None)

    @classmethod
    def from_yaml(cls, path: Path) -> Settings:
        """Load settings from a YAML file."""
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content) or {}
        return cls.model_validate(data)

    @classmethod
    def load(cls, path: Path | None = None) -> Settings:
        """Load settings from file or environment."""
        if path and path.exists():
            return cls.from_yaml(path)

        config_dir = Path.home() / ".myagent"
        config_file = config_dir / "config.yaml"
        if config_file.exists():
            return cls.from_yaml(config_file)

        return cls()

    def model_post_init(self, __context: Any) -> None:
        """Apply environment variable overrides."""
        if env_model := os.environ.get("MYAGENT_MODEL_DEFAULT"):
            self.model.default = env_model
        if env_turns := os.environ.get("MYAGENT_CONTEXT_MAX_TURNS"):
            try:
                self.context.max_turns = int(env_turns)
            except ValueError:
                pass
        if env_github := os.environ.get("GITHUB_TOKEN"):
            self.github_token = env_github

    def get_provider_api_key(self, provider: str) -> str | None:
        """Get API key for a provider from config or environment."""
        env_map: dict[str, str] = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "zhipu": "ZHIPU_API_KEY",
            "moonshot": "MOONSHOT_API_KEY",
            "minimax": "MINIMAX_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "xai": "XAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "alibaba": "DASHSCOPE_API_KEY",
            "huggingface": "HF_API_KEY",
            "nvidia": "NVIDIA_API_KEY",
            "arcee": "ARCEE_API_KEY",
            "xiaomi": "XIAOMI_API_KEY",
        }
        env_var = env_map.get(provider)
        if env_var:
            return os.environ.get(env_var) or None
        return None
