"""Moonshot (Kimi/月之暗面) provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class MoonshotProvider(OpenAIProvider):
    """Provider for Moonshot (Kimi) API (OpenAI-compatible).

    Supports models:
    - moonshot-v1-8k
    - moonshot-v1-32k
    - moonshot-v1-128k
    - moonshot-v1-auto
    """

    name = "moonshot"

    def __init__(
        self,
        api_key: str,
        model: str = "moonshot-v1-8k",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.moonshot.cn/v1",
            **kwargs,
        )
