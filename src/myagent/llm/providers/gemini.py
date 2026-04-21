"""Google Gemini provider for MyAgent.

Uses Gemini API (OpenAI-compatible endpoint).
"""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class GeminiProvider(OpenAIProvider):
    """Provider for Google Gemini API (OpenAI-compatible).

    Supports models:
    - gemini-1.5-pro
    - gemini-1.5-flash
    - gemini-1.5-pro-latest
    - gemini-1.5-flash-latest
    """

    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-pro",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://generativelanguage.googleapis.com/v1beta/openai",
            **kwargs,
        )
