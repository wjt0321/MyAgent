"""Tests for config hot-reload."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

import pytest

from myagent.config.hot_reload import ConfigWatcher


class TestConfigWatcher:
    def test_creation(self):
        watcher = ConfigWatcher(check_interval=0.1)
        assert watcher.check_interval == 0.1
        assert watcher._running is False

    def test_watch_file(self):
        watcher = ConfigWatcher(check_interval=0.1)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            path = Path(f.name)

        callback_called = [False]

        def callback():
            callback_called[0] = True

        watcher.watch(path, callback)
        assert path.resolve() in watcher._watched_files

        # Clean up
        path.unlink()

    def test_file_change_detection(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            path = Path(f.name)

        watcher = ConfigWatcher(check_interval=0.1)
        callback_called = [False]

        def callback():
            callback_called[0] = True

        watcher.watch(path, callback)
        watcher.start()

        try:
            # Wait for initial check
            time.sleep(0.15)

            # Modify file
            path.write_text('{"updated": true}')

            # Wait for detection
            time.sleep(0.2)

            assert callback_called[0] is True
        finally:
            watcher.stop()
            path.unlink()

    def test_unwatch(self):
        watcher = ConfigWatcher(check_interval=0.1)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            path = Path(f.name)

        watcher.watch(path, lambda: None)
        watcher.unwatch(path)
        assert path.resolve() not in watcher._watched_files

        path.unlink()

    def test_multiple_callbacks(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            path = Path(f.name)

        watcher = ConfigWatcher(check_interval=0.1)
        calls = []

        def callback1():
            calls.append(1)

        def callback2():
            calls.append(2)

        watcher.watch(path, callback1)
        watcher.watch(path, callback2)
        watcher.start()

        try:
            time.sleep(0.15)
            path.write_text('{"updated": true}')
            time.sleep(0.2)

            assert 1 in calls
            assert 2 in calls
        finally:
            watcher.stop()
            path.unlink()
