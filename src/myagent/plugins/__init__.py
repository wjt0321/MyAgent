"""MyAgent plugin system."""

from myagent.plugins.api import PluginAPI
from myagent.plugins.hooks import HookCallback, HookContext, HookPoint, HookRegistry
from myagent.plugins.manifest import PluginManifest

__all__ = [
    "HookCallback",
    "HookContext",
    "HookPoint",
    "HookRegistry",
    "PluginAPI",
    "PluginManifest",
]
