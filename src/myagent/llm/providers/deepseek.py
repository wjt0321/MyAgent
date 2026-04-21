"""DeepSeek API provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class DeepSeekProvider(OpenAIProvider):
    """Provider for DeepSeek API (OpenAI-compatible).

    Supports models:
    - deepseek-chat (DeepSeek-V3)
    - deepseek-reasoner (DeepSeek-R1)
    """

    name = "deepseek"

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.deepseek.com/v1",
            **kwargs,
        )
