"""Plugin loader for MyAgent."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from myagent.plugins.api import PluginAPI
from myagent.plugins.manifest import PluginManifest


class PluginLoader:
    """Loads plugins by importing their entry modules and calling register()."""

    def __init__(self) -> None:
        self.loaded_plugins: dict[str, PluginAPI] = {}

    def load(self, manifest: PluginManifest) -> PluginAPI | None:
        """Load a plugin and return its API if successful."""
        if manifest._plugin_dir is None:
            return None

        entry_path = manifest._plugin_dir / manifest.entry
        if not entry_path.exists():
            return None

        try:
            module = self._import_module(entry_path, manifest.id)
            if module is None:
                return None

            api = PluginAPI(manifest.id)

            register_fn = getattr(module, "register", None)
            if register_fn is not None and callable(register_fn):
                register_fn(api)

            self.loaded_plugins[manifest.id] = api
            return api

        except Exception:
            return None

    def _import_module(self, path: Path, plugin_id: str) -> ModuleType | None:
        """Dynamically import a plugin module from file path."""
        module_name = f"myagent_plugin_{plugin_id.replace('-', '_')}"

        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return None

        if module_name in sys.modules:
            del sys.modules[module_name]

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def unload(self, plugin_id: str) -> None:
        """Unload a plugin and remove its module."""
        self.loaded_plugins.pop(plugin_id, None)
        module_name = f"myagent_plugin_{plugin_id.replace('-', '_')}"
        sys.modules.pop(module_name, None)
