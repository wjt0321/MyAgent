"""Arcee AI provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class ArceeProvider(OpenAIProvider):
    """Provider for Arcee AI API (OpenAI-compatible).

    Supports models:
    - trinity-large-thinking
    - trinity-large-preview
    - trinity-mini
    """

    name = "arcee"

    def __init__(
        self,
        api_key: str,
        model: str = "trinity-large-thinking",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.arcee.ai/v1",
            **kwargs,
        )
