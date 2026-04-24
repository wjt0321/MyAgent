"""Xiaomi MiMo provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class XiaomiProvider(OpenAIProvider):
    """Provider for Xiaomi MiMo API (OpenAI-compatible).

    Supports models:
    - mimo-v2-pro
    - mimo-v2-omni
    - mimo-v2-flash
    """

    name = "xiaomi"

    def __init__(
        self,
        api_key: str,
        model: str = "mimo-v2-pro",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.mimo.ai/v1",
            **kwargs,
        )
