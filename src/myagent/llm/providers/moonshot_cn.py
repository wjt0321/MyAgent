"""Moonshot (Kimi) China provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class MoonshotCNProvider(OpenAIProvider):
    """Provider for Moonshot (Kimi) China Domestic API (OpenAI-compatible).

    China domestic endpoint for mainland China users.
    API Endpoint: https://api.moonshot.cn/v1
    Note: API Key is NOT interchangeable with international version.

    Supports models:
    - moonshot-v1-8k
    - moonshot-v1-32k
    - moonshot-v1-128k
    - moonshot-v1-auto
    """

    name = "moonshot-cn"

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
