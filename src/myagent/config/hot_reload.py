"""Configuration hot-reload support for MyAgent.

Watches configuration files and reloads settings without restart.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfigWatcher:
    """Watch configuration files for changes and trigger callbacks."""

    def __init__(self, check_interval: float = 5.0) -> None:
        self.check_interval = check_interval
        self._watched_files: Dict[Path, float] = {}
        self._callbacks: Dict[Path, List[Callable[[], None]]] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def watch(self, path: Path, callback: Callable[[], None]) -> None:
        """Watch a file for changes."""
        path = path.resolve()
        with self._lock:
            if path not in self._watched_files:
                self._watched_files[path] = self._get_mtime(path)
            if path not in self._callbacks:
                self._callbacks[path] = []
            self._callbacks[path].append(callback)
        logger.debug("Watching config file: %s", path)

    def unwatch(self, path: Path) -> None:
        """Stop watching a file."""
        path = path.resolve()
        with self._lock:
            self._watched_files.pop(path, None)
            self._callbacks.pop(path, None)

    def start(self) -> None:
        """Start the watcher thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info("Config watcher started")

    def stop(self) -> None:
        """Stop the watcher thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.check_interval + 1)
        logger.info("Config watcher stopped")

    def _get_mtime(self, path: Path) -> float:
        """Get file modification time."""
        try:
            return path.stat().st_mtime
        except (OSError, FileNotFoundError):
            return 0.0

    def _watch_loop(self) -> None:
        """Main watch loop."""
        while self._running:
            with self._lock:
                files = list(self._watched_files.items())

            for path, last_mtime in files:
                current_mtime = self._get_mtime(path)
                if current_mtime > last_mtime:
                    logger.info("Config file changed: %s", path)
                    with self._lock:
                        self._watched_files[path] = current_mtime
                        callbacks = self._callbacks.get(path, [])

                    for callback in callbacks:
                        try:
                            callback()
                        except Exception as e:
                            logger.error("Config reload callback failed: %s", e)

            time.sleep(self.check_interval)


# Global watcher instance
_global_watcher: Optional[ConfigWatcher] = None


def get_watcher() -> ConfigWatcher:
    """Get the global config watcher."""
    global _global_watcher
    if _global_watcher is None:
        _global_watcher = ConfigWatcher()
    return _global_watcher
