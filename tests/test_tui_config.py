"""Tests for TUI configuration persistence."""

from __future__ import annotations

import tempfile
from pathlib import Path

from myagent.tui.app import MyAgentApp


class TestTUIConfigPersistence:
    def test_config_loaded_on_init(self):
        """App should load config on initialization."""
        app = MyAgentApp()
        assert app._config is not None

    def test_config_is_empty_when_file_missing(self):
        """Missing config file should leave config empty until setup completes."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            app = MyAgentApp()
            app._config_path = config_path
            app._load_config()
            assert app._config == {}

    def test_save_and_load_config(self):
        """Config should be saved and loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            app = MyAgentApp()
            app._config_path = config_path
            app._config = {"agent": "worker", "model": "glm-5.1"}
            app._save_config()

            assert config_path.exists()

            app2 = MyAgentApp()
            app2._config_path = config_path
            app2._load_config()
            assert app2._config["agent"] == "worker"
            assert app2._config["model"] == "glm-5.1"
