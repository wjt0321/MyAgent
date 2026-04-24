"""Ollama provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class OllamaProvider(OpenAIProvider):
    """Provider for Ollama local API (OpenAI-compatible).

    Supports any model running locally via Ollama:
    - llama3.3
    - qwen2.5
    - deepseek-coder-v2
    - codellama
    - mistral
    - gemma2
    - phi4
    """

    name = "ollama"

    def __init__(
        self,
        api_key: str = "ollama",
        model: str = "llama3.3",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "http://localhost:11434/v1",
            **kwargs,
        )
