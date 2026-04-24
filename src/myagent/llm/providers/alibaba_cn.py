"""Alibaba Cloud (DashScope) China provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class AlibabaCNProvider(OpenAIProvider):
    """Provider for Alibaba Cloud DashScope China Domestic API (OpenAI-compatible).

    China domestic endpoint for mainland China users.
    Console: https://help.aliyun.com/zh/model-studio/
    API Endpoint: https://dashscope.aliyuncs.com/compatible-mode/v1
    Note: API Key is NOT interchangeable with international version.

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

    name = "alibaba-cn"

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
            base_url=base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            **kwargs,
        )
