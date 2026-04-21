"""Alibaba Qwen provider for MyAgent.

Uses DashScope API (OpenAI-compatible).
"""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class QwenProvider(OpenAIProvider):
    """Provider for Alibaba Qwen/DashScope API (OpenAI-compatible).

    Supports models:
    - qwen-max
    - qwen-plus
    - qwen-turbo
    - qwen-coder-plus
    - qwen2.5-72b-instruct
    """

    name = "qwen"

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
