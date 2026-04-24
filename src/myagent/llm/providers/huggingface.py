"""Hugging Face provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class HuggingFaceProvider(OpenAIProvider):
    """Provider for Hugging Face Inference API (OpenAI-compatible).

    Supports models:
    - meta-llama/Llama-3.3-70B-Instruct
    - mistralai/Mistral-Large-Instruct-2407
    - Qwen/Qwen2.5-72B-Instruct
    - deepseek-ai/DeepSeek-V3
    - NousResearch/Hermes-3-Llama-3.1-70B
    """

    name = "huggingface"

    def __init__(
        self,
        api_key: str,
        model: str = "meta-llama/Llama-3.3-70B-Instruct",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api-inference.huggingface.co/v1",
            **kwargs,
        )
