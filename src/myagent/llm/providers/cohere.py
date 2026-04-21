"""Cohere provider for MyAgent.

Uses Cohere Chat API.
"""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class CohereProvider(OpenAIProvider):
    """Provider for Cohere API (OpenAI-compatible).

    Supports models:
    - command-r
    - command-r-plus
    - command
    - command-light
    """

    name = "cohere"

    def __init__(
        self,
        api_key: str,
        model: str = "command-r",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.cohere.com/v1",
            **kwargs,
        )
