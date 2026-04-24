"""Baidu ERNIE (文心一言) provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class BaiduProvider(OpenAIProvider):
    """Provider for Baidu ERNIE API (OpenAI-compatible).

    Console: https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application
    API Endpoint: https://qianfan.baidubce.com/v2

    Supports models:
    - ernie-4.0-8k-latest
    - ernie-4.0-turbo-8k
    - ernie-3.5-8k
    - ernie-speed-8k
    - ernie-lite-8k
    - ernie-tiny-8k
    """

    name = "baidu"

    def __init__(
        self,
        api_key: str,
        model: str = "ernie-4.0-8k-latest",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://qianfan.baidubce.com/v2",
            **kwargs,
        )
