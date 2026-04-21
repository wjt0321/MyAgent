"""Ollama provider for MyAgent.

Local LLM inference via Ollama API.
"""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class OllamaProvider(OpenAIProvider):
    """Provider for Ollama local inference (OpenAI-compatible).

    Supports any model available in Ollama:
    - llama3.3
    - qwen2.5
    - deepseek-r1
    - phi4
    - mistral
    - codellama
    """

    name = "ollama"

    def __init__(
        self,
        api_key: str = "ollama",  # Ollama doesn't require API key
        model: str = "llama3.2",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "http://localhost:11434/v1",
            **kwargs,
        )
