"""OpenRouter provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class OpenRouterProvider(OpenAIProvider):
    """Provider for OpenRouter API (OpenAI-compatible)."""

    name = "openrouter"

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://openrouter.ai/api/v1",
            **kwargs,
        )
