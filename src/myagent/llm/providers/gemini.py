"""Google Gemini provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class GeminiProvider(OpenAIProvider):
    """Provider for Google Gemini API (OpenAI-compatible).

    Supports models:
    - gemini-2.5-pro
    - gemini-2.5-flash
    - gemini-2.5-flash-lite
    - gemini-2.0-pro
    - gemini-2.0-flash
    - gemini-2.0-flash-lite
    - gemini-1.5-pro
    - gemini-1.5-flash
    """

    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-pro",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://generativelanguage.googleapis.com/v1beta/openai",
            **kwargs,
        )
