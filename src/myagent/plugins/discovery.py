"""Plugin discovery for MyAgent."""

from __future__ import annotations

from pathlib import Path

from myagent.plugins.manifest import PluginManifest


MANIFEST_FILENAME = "myagent-plugin.yaml"


class PluginDiscovery:
    """Discovers plugins from directories."""

    def __init__(self, search_paths: list[Path]) -> None:
        self.search_paths = search_paths

    def discover(self) -> list[PluginManifest]:
        """Discover all plugins in search paths."""
        manifests: list[PluginManifest] = []
        seen_ids: set[str] = set()

        for path in self.search_paths:
            if not path.exists() or not path.is_dir():
                continue

            for item in path.iterdir():
                if not item.is_dir():
                    continue

                manifest_path = item / MANIFEST_FILENAME
                if not manifest_path.exists():
                    continue

                try:
                    manifest = PluginManifest.from_file(manifest_path)
                    if manifest.id not in seen_ids:
                        manifests.append(manifest)
                        seen_ids.add(manifest.id)
                except Exception:
                    continue

        return manifests


def discover_plugins(search_paths: list[Path]) -> list[PluginManifest]:
    """Convenience function to discover plugins from search paths."""
    discovery = PluginDiscovery(search_paths)
    return discovery.discover()
