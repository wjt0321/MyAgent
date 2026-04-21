"""Plugin registry for MyAgent."""

from __future__ import annotations

from myagent.plugins.manifest import PluginManifest


class PluginRegistry:
    """Registry for loaded plugin manifests."""

    def __init__(self) -> None:
        self._plugins: dict[str, PluginManifest] = {}

    def register(self, manifest: PluginManifest) -> None:
        """Register a plugin manifest."""
        self._plugins[manifest.id] = manifest

    def get(self, plugin_id: str) -> PluginManifest | None:
        """Get a plugin manifest by ID."""
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> list[PluginManifest]:
        """List all registered plugin manifests."""
        return list(self._plugins.values())

    def unregister(self, plugin_id: str) -> None:
        """Remove a plugin from the registry."""
        self._plugins.pop(plugin_id, None)

    def __contains__(self, plugin_id: str) -> bool:
        return plugin_id in self._plugins
