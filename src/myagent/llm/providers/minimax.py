"""MiniMax provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class MiniMaxProvider(OpenAIProvider):
    """Provider for MiniMax API (OpenAI-compatible).

    Supports models:
    - abab6.5s-chat
    - abab6.5-chat
    - abab5.5s-chat
    - abab5.5-chat
    """

    name = "minimax"

    def __init__(
        self,
        api_key: str,
        model: str = "abab6.5s-chat",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.minimax.chat/v1",
            **kwargs,
        )
