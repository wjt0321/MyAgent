"""Tencent Hunyuan (腾讯混元) provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class HunyuanProvider(OpenAIProvider):
    """Provider for Tencent Hunyuan API (OpenAI-compatible).

    Console: https://console.cloud.tencent.com/hunyuan
    API Endpoint: https://hunyuan.tencentcloudapi.com/v1

    Supports models:
    - hunyuan-pro
    - hunyuan-standard
    - hunyuan-lite
    - hunyuan-vision
    - hunyuan-code
    """

    name = "hunyuan"

    def __init__(
        self,
        api_key: str,
        model: str = "hunyuan-pro",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://hunyuan.tencentcloudapi.com/v1",
            **kwargs,
        )
