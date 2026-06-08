"""Smart context window management for MyAgent.

Provides:
- Automatic detection of model context windows
- Token estimation
- Configuration override support
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from myagent.config.settings import Settings

logger = logging.getLogger(__name__)


# Known model context window limits (tokens)
KNOWN_CONTEXT_WINDOWS: dict[str, int] = {
    # Anthropic Claude
    "claude-3-5-sonnet": 200000,
    "claude-3-5-haiku": 200000,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    "claude-2": 100000,
    "claude-2.1": 200000,
    # OpenAI GPT
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-3.5-turbo": 16384,
    "gpt-3.5-turbo-16k": 16384,
    # DeepSeek
    "deepseek-chat": 128000,
    "deepseek-coder": 128000,
    # Qwen
    "qwen-max": 32768,
    "qwen-plus": 32768,
    "qwen-turbo": 8192,
    # Zhipu
    "glm-4": 128000,
    "glm-4-plus": 128000,
    "glm-4-flash": 128000,
    # Moonshot
    "moonshot-v1-8k": 8192,
    "moonshot-v1-32k": 32768,
    "moonshot-v1-128k": 128000,
    # Aliyun
    "qwen2.5-max": 128000,
    "qwen2.5-plus": 32768,
}


# Default fallback context window
DEFAULT_CONTEXT_WINDOW = 128000


@dataclass
class ModelContext:
    """Model context window configuration."""

    model: str
    """Name of the model."""

    provider: str
    """Name of the provider."""

    max_tokens: int
    """Maximum total tokens (prompt + response)."""

    max_output_tokens: int | None = None
    """Maximum tokens in the response (if known)."""

    estimated_max_input: int | None = None
    """Estimated maximum input tokens (max_tokens minus buffer)."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the model."""

    def __post_init__(self) -> None:
        if self.estimated_max_input is None:
            # Reserve ~40% for output by default
            self.estimated_max_input = int(self.max_tokens * 0.6)


class ContextWindowManager:
    """Manager for model context windows."""

    def __init__(self) -> None:
        self._model_cache: dict[str, ModelContext] = {}
        self._settings: Settings | None = None

    def _get_settings(self) -> Settings:
        """Lazy load settings."""
        if self._settings is None:
            self._settings = Settings.load()
        return self._settings

    def get_context_window(
        self,
        model: str,
        provider: str = "unknown"
    ) -> ModelContext:
        """Get the context window configuration for a model.

        Checks (in order):
        1. In-memory cache
        2. User configuration overrides
        3. Known model database
        4. Default fallback

        Args:
            model: The name of the model.
            provider: The name of the provider (for logging).

        Returns:
            The ModelContext configuration.
        """
        cache_key = f"{provider}:{model}"

        if cache_key in self._model_cache:
            return self._model_cache[cache_key]

        # Check for user config override
        settings = self._get_settings()
        if hasattr(settings, "model_context_overrides"):
            overrides = settings.model_context_overrides or {}
            if model in overrides:
                config = overrides[model]
                if isinstance(config, dict):
                    ctx = ModelContext(
                        model=model,
                        provider=provider,
                        max_tokens=config.get("max_tokens", DEFAULT_CONTEXT_WINDOW),
                        max_output_tokens=config.get("max_output_tokens"),
                    )
                    self._model_cache[cache_key] = ctx
                    logger.debug(
                        f"Using configured context window for {model}: {ctx.max_tokens}"
                    )
                    return ctx
                elif isinstance(config, int):
                    ctx = ModelContext(
                        model=model,
                        provider=provider,
                        max_tokens=config,
                    )
                    self._model_cache[cache_key] = ctx
                    logger.debug(
                        f"Using configured context window for {model}: {ctx.max_tokens}"
                    )
                    return ctx

        # Check known model database
        for pattern, max_tokens in KNOWN_CONTEXT_WINDOWS.items():
            if pattern.lower() in model.lower():
                ctx = ModelContext(
                    model=model,
                    provider=provider,
                    max_tokens=max_tokens,
                )
                self._model_cache[cache_key] = ctx
                logger.debug(
                    f"Using known context window for {model}: {ctx.max_tokens}"
                )
                return ctx

        # Fallback to default
        ctx = ModelContext(
            model=model,
            provider=provider,
            max_tokens=DEFAULT_CONTEXT_WINDOW,
        )
        self._model_cache[cache_key] = ctx
        logger.debug(
            f"Using default context window for {model}: {ctx.max_tokens}"
        )
        return ctx

    def estimate_text_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string.

        Uses a simple heuristic: ~4 characters per token for English,
        ~2 characters per token for Chinese.

        Args:
            text: The text to estimate.

        Returns:
            Estimated token count.
        """
        if not text:
            return 0

        # Rough estimate
        # Chinese characters are ~1 token per 1.5 chars
        # English is ~1 token per 4 chars
        # Mixed content average is ~1 token per 3 chars
        return max(1, len(text) // 3)

    def get_safe_limit(
        self,
        model: str,
        provider: str = "unknown",
        buffer_ratio: float = 0.2
    ) -> int:
        """Get a safe token limit for prompts.

        Args:
            model: The name of the model.
            provider: The name of the provider.
            buffer_ratio: Ratio of context window to reserve for output.

        Returns:
            Safe token limit for input.
        """
        ctx = self.get_context_window(model, provider)
        return int(ctx.max_tokens * (1 - buffer_ratio))

    def clear_cache(self) -> None:
        """Clear the model cache."""
        self._model_cache.clear()


# Singleton instance
_default_manager: ContextWindowManager | None = None


def get_context_window_manager() -> ContextWindowManager:
    """Get the global ContextWindowManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ContextWindowManager()
    return _default_manager
