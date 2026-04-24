"""iFlytek Spark (讯飞星火) provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class SparkProvider(OpenAIProvider):
    """Provider for iFlytek Spark API (OpenAI-compatible).

    Console: https://xinghuo.xfyun.cn/sparkapi
    API Endpoint: https://spark-api-open.xf-yun.com/v1

    Supports models:
    - generalv4
    - pro-128k
    - max-32k
    - lite
    """

    name = "spark"

    def __init__(
        self,
        api_key: str,
        model: str = "generalv4",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://spark-api-open.xf-yun.com/v1",
            **kwargs,
        )
