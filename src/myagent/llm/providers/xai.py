"""xAI (Grok) provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class XAIProvider(OpenAIProvider):
    """Provider for xAI API (OpenAI-compatible).

    Supports models:
    - grok-4.20-reasoning
    - grok-4-1-fast-reasoning
    - grok-3
    - grok-3-fast
    - grok-3-mini
    """

    name = "xai"

    def __init__(
        self,
        api_key: str,
        model: str = "grok-3",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.x.ai/v1",
            **kwargs,
        )
