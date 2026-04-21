"""Tests for PluginSystem."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from myagent.plugins.api import PluginAPI
from myagent.plugins.discovery import PluginDiscovery
from myagent.plugins.loader import PluginLoader
from myagent.plugins.manifest import PluginManifest
from myagent.plugins.registry import PluginRegistry


class TestPluginManifest:
    def test_manifest_from_dict(self):
        data = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "entry": "plugin.py",
        }
        manifest = PluginManifest.model_validate(data)
        assert manifest.id == "test-plugin"
        assert manifest.name == "Test Plugin"
        assert manifest.version == "1.0.0"
        assert manifest.entry == "plugin.py"

    def test_manifest_defaults(self):
        data = {"id": "minimal", "name": "Minimal"}
        manifest = PluginManifest.model_validate(data)
        assert manifest.version == "0.1.0"
        assert manifest.entry == "plugin.py"
        assert manifest.tools == []
        assert manifest.agents == []
        assert manifest.hooks == {}

    def test_manifest_load_from_yaml(self, tmp_path: Path):
        yaml_content = """
id: yaml-plugin
name: YAML Plugin
version: 1.2.3
entry: main.py
tools:
  - MyTool
agents:
  - my-agent.md
"""
        manifest_path = tmp_path / "myagent-plugin.yaml"
        manifest_path.write_text(yaml_content, encoding="utf-8")

        manifest = PluginManifest.from_file(manifest_path)
        assert manifest.id == "yaml-plugin"
        assert manifest.version == "1.2.3"
        assert manifest.tools == ["MyTool"]
        assert manifest.agents == ["my-agent.md"]


class TestPluginDiscovery:
    def test_discover_plugins(self, tmp_path: Path):
        plugin_dir = tmp_path / "plugins"
        plugin1 = plugin_dir / "plugin-a"
        plugin1.mkdir(parents=True)
        (plugin1 / "myagent-plugin.yaml").write_text(
            "id: plugin-a\nname: Plugin A\n", encoding="utf-8"
        )

        plugin2 = plugin_dir / "plugin-b"
        plugin2.mkdir(parents=True)
        (plugin2 / "myagent-plugin.yaml").write_text(
            "id: plugin-b\nname: Plugin B\n", encoding="utf-8"
        )

        non_plugin = plugin_dir / "not-a-plugin"
        non_plugin.mkdir()

        discovery = PluginDiscovery([plugin_dir])
        manifests = discovery.discover()

        assert len(manifests) == 2
        ids = {m.id for m in manifests}
        assert ids == {"plugin-a", "plugin-b"}

    def test_discover_empty_directory(self, tmp_path: Path):
        discovery = PluginDiscovery([tmp_path])
        manifests = discovery.discover()
        assert len(manifests) == 0

    def test_discover_nonexistent_directory(self, tmp_path: Path):
        discovery = PluginDiscovery([tmp_path / "does-not-exist"])
        manifests = discovery.discover()
        assert len(manifests) == 0


class TestPluginRegistry:
    def test_register_plugin(self):
        registry = PluginRegistry()
        manifest = PluginManifest(id="test", name="Test")
        registry.register(manifest)
        assert registry.get("test") is manifest

    def test_get_nonexistent(self):
        registry = PluginRegistry()
        assert registry.get("nonexistent") is None

    def test_list_plugins(self):
        registry = PluginRegistry()
        registry.register(PluginManifest(id="a", name="A"))
        registry.register(PluginManifest(id="b", name="B"))
        plugins = registry.list_plugins()
        assert len(plugins) == 2
        assert {p.id for p in plugins} == {"a", "b"}

    def test_unregister(self):
        registry = PluginRegistry()
        registry.register(PluginManifest(id="test", name="Test"))
        registry.unregister("test")
        assert registry.get("test") is None

    def test_duplicate_registration_overwrites(self):
        registry = PluginRegistry()
        m1 = PluginManifest(id="test", name="Test1")
        m2 = PluginManifest(id="test", name="Test2")
        registry.register(m1)
        registry.register(m2)
        assert registry.get("test").name == "Test2"


class TestPluginAPI:
    def test_api_creation(self):
        api = PluginAPI("test-plugin")
        assert api.plugin_id == "test-plugin"

    def test_api_register_tool(self):
        api = PluginAPI("test-plugin")
        tool = MagicMock()
        tool.name = "MyTool"
        api.register_tool(tool)
        assert api.tools == [tool]

    def test_api_register_agent(self):
        api = PluginAPI("test-plugin")
        api.register_agent("my-agent", "system prompt")
        assert "my-agent" in api.agents
        assert api.agents["my-agent"] == "system prompt"

    def test_api_register_hook(self):
        api = PluginAPI("test-plugin")
        handler = MagicMock()
        api.register_hook("SESSION_START", handler)
        assert api.hooks["SESSION_START"] == handler


class TestPluginLoader:
    def test_loader_init(self):
        loader = PluginLoader()
        assert loader.loaded_plugins == {}

    def test_load_plugin_with_no_register(self, tmp_path: Path):
        plugin_dir = tmp_path / "my-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "myagent-plugin.yaml").write_text(
            "id: my-plugin\nname: My Plugin\nentry: plugin.py\n", encoding="utf-8"
        )
        (plugin_dir / "plugin.py").write_text(
            "# No register function\n", encoding="utf-8"
        )

        manifest = PluginManifest(id="my-plugin", name="My Plugin", entry="plugin.py")
        manifest._plugin_dir = plugin_dir

        loader = PluginLoader()
        api = loader.load(manifest)

        assert api.plugin_id == "my-plugin"
        assert api.tools == []

    def test_load_plugin_with_register(self, tmp_path: Path):
        plugin_dir = tmp_path / "my-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "myagent-plugin.yaml").write_text(
            "id: my-plugin\nname: My Plugin\nentry: plugin.py\n", encoding="utf-8"
        )

        plugin_py = plugin_dir / "plugin.py"
        plugin_py.write_text(
            "def register(api):\n    api.metadata['registered'] = True\n",
            encoding="utf-8",
        )

        manifest = PluginManifest(id="my-plugin", name="My Plugin", entry="plugin.py")
        manifest._plugin_dir = plugin_dir

        loader = PluginLoader()
        api = loader.load(manifest)

        assert api.plugin_id == "my-plugin"
        assert api.metadata.get("registered") is True

    def test_load_plugin_import_error(self, tmp_path: Path):
        plugin_dir = tmp_path / "bad-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "myagent-plugin.yaml").write_text(
            "id: bad-plugin\nname: Bad Plugin\nentry: nonexistent.py\n", encoding="utf-8"
        )

        manifest = PluginManifest(id="bad-plugin", name="Bad Plugin", entry="nonexistent.py")
        manifest._plugin_dir = plugin_dir

        loader = PluginLoader()
        api = loader.load(manifest)

        assert api is None

    def test_load_plugin_register_error(self, tmp_path: Path):
        plugin_dir = tmp_path / "err-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "myagent-plugin.yaml").write_text(
            "id: err-plugin\nname: Err Plugin\nentry: plugin.py\n", encoding="utf-8"
        )
        (plugin_dir / "plugin.py").write_text(
            "def register(api):\n    raise ValueError('Registration failed')\n",
            encoding="utf-8",
        )

        manifest = PluginManifest(id="err-plugin", name="Err Plugin", entry="plugin.py")
        manifest._plugin_dir = plugin_dir

        loader = PluginLoader()
        api = loader.load(manifest)

        assert api is None
