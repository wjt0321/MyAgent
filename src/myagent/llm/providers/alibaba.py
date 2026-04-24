"""Alibaba Cloud (DashScope) provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class AlibabaProvider(OpenAIProvider):
    """Provider for Alibaba Cloud DashScope API (OpenAI-compatible).

    Supports models:
    - qwen-max
    - qwen-plus
    - qwen-turbo
    - qwen-coder-plus
    - qwen-coder-next
    - qwen2.5-72b-instruct
    - qwen2.5-14b-instruct
    - qwq-32b
    """

    name = "alibaba"

    def __init__(
        self,
        api_key: str,
        model: str = "qwen-max",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            **kwargs,
        )
