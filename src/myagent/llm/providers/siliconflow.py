"""SiliconFlow provider for MyAgent.

Chinese cloud LLM platform with many open-source models.
"""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class SiliconFlowProvider(OpenAIProvider):
    """Provider for SiliconFlow API (OpenAI-compatible).

    Supports models:
    - deepseek-ai/DeepSeek-V3
    - deepseek-ai/DeepSeek-R1
    - Qwen/Qwen2.5-72B-Instruct
    - meta-llama/Llama-3.3-70B-Instruct
    - THUDM/glm-4-9b-chat
    """

    name = "siliconflow"

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-ai/DeepSeek-V3",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.siliconflow.cn/v1",
            **kwargs,
        )
