"""Plugin manifest for MyAgent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, PrivateAttr


class PluginManifest(BaseModel):
    """Plugin manifest defining metadata and entry point."""

    id: str = Field(description="Unique plugin identifier")
    name: str = Field(description="Human-readable plugin name")
    version: str = Field(default="0.1.0", description="Plugin version")
    description: str | None = Field(default=None, description="Plugin description")
    entry: str = Field(default="plugin.py", description="Main Python entry file")
    tools: list[str] = Field(default_factory=list, description="Tool module names")
    agents: list[str] = Field(default_factory=list, description="Agent markdown files")
    hooks: dict[str, str] = Field(default_factory=dict, description="Hook name → handler function")
    dependencies: list[str] = Field(default_factory=list, description="Python package dependencies")
    config_schema: dict[str, Any] | None = Field(default=None, description="Configuration JSON schema")

    _plugin_dir: Path | None = PrivateAttr(default=None)

    @classmethod
    def from_file(cls, path: Path) -> PluginManifest:
        """Load manifest from a YAML file."""
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content) or {}
        manifest = cls.model_validate(data)
        manifest._plugin_dir = path.parent
        return manifest
