"""ByteDance Doubao (字节豆包) provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class DoubaoProvider(OpenAIProvider):
    """Provider for ByteDance Volcengine Doubao API (OpenAI-compatible).

    Console: https://console.volcengine.com/ark/region:ark+cn-beijing/model
    API Endpoint: https://ark.cn-beijing.volces.com/api/v3

    Supports models:
    - doubao-pro-256k
    - doubao-pro-128k
    - doubao-pro-32k
    - doubao-lite-128k
    - doubao-lite-32k
    - doubao-vision-pro-32k
    """

    name = "doubao"

    def __init__(
        self,
        api_key: str,
        model: str = "doubao-pro-256k",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://ark.cn-beijing.volces.com/api/v3",
            **kwargs,
        )
