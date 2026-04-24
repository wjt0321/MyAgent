"""NVIDIA NIM provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class NvidiaProvider(OpenAIProvider):
    """Provider for NVIDIA NIM API (OpenAI-compatible).

    Supports models:
    - nvidia/llama-3.3-nemotron-super-49b-v1
    - nvidia/nemotron-4-340b-instruct
    - meta/llama-3.3-70b-instruct
    - meta/llama-3.1-405b-instruct
    - qwen/qwen2.5-72b-instruct
    - deepseek-ai/deepseek-v3
    """

    name = "nvidia"

    def __init__(
        self,
        api_key: str,
        model: str = "nvidia/llama-3.3-nemotron-super-49b-v1",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://integrate.api.nvidia.com/v1",
            **kwargs,
        )
