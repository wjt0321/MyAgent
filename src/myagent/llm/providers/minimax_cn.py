"""MiniMax China provider for MyAgent."""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class MiniMaxCNProvider(OpenAIProvider):
    """Provider for MiniMax China Domestic API (OpenAI-compatible).

    China domestic endpoint for mainland China users.
    Console: https://platform.minimax.chat/
    Note: API Key is NOT interchangeable with international version.

    Supports models:
    - abab6.5s-chat
    - abab6.5-chat
    - abab5.5s-chat
    - abab5.5-chat
    """

    name = "minimax-cn"

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
            base_url=base_url or "https://api.minimaxi.com/v1",
            **kwargs,
        )
