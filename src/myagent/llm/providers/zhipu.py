"""ZhipuAI (智谱AI) provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class ZhipuProvider(OpenAIProvider):
    """Provider for ZhipuAI (智谱AI) API (OpenAI-compatible).

    Supports models:
    - glm-4 (GLM-4)
    - glm-4-plus (GLM-4 Plus)
    - glm-4-flash (GLM-4 Flash)
    - glm-4v (GLM-4V)
    - glm-3-turbo (ChatGLM3 Turbo)
    - glm-5.1 (GLM-5.1)
    - glm-5-Turbo (GLM-5 Turbo)
    - glm-4.7 (GLM-4.7)
    """

    name = "zhipu"

    def __init__(
        self,
        api_key: str,
        model: str = "glm-4",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://open.bigmodel.cn/api/paas/v4",
            **kwargs,
        )
