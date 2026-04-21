"""Tests for myagent config."""

from pathlib import Path

import pytest

from myagent.config.settings import Settings


class TestSettings:
    def test_settings_defaults(self):
        settings = Settings()
        assert settings.model.default == "anthropic/claude-sonnet-4"
        assert settings.context.max_turns == 50
        assert settings.memory.enabled is True

    def test_settings_from_dict(self):
        data = {
            "model": {"default": "openai/gpt-4o"},
            "context": {"max_turns": 30},
        }
        settings = Settings.model_validate(data)
        assert settings.model.default == "openai/gpt-4o"
        assert settings.context.max_turns == 30

    def test_settings_load_from_yaml(self, tmp_path: Path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
model:
  default: "openai/gpt-4o"
context:
  max_turns: 20
memory:
  enabled: false
""",
            encoding="utf-8",
        )

        settings = Settings.from_yaml(config_file)
        assert settings.model.default == "openai/gpt-4o"
        assert settings.context.max_turns == 20
        assert settings.memory.enabled is False

    def test_settings_env_override(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MYAGENT_MODEL_DEFAULT", "custom-model")
        monkeypatch.setenv("MYAGENT_CONTEXT_MAX_TURNS", "100")

        settings = Settings()
        assert settings.model.default == "custom-model"
        assert settings.context.max_turns == 100
