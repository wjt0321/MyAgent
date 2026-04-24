"""Retry utilities for LLM providers with exponential backoff."""

from __future__ import annotations

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator for retrying async functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        retryable_exceptions: Tuple of exception types to retry on

    Example:
        @retry_with_backoff(
            max_retries=3,
            base_delay=1.0,
            retryable_exceptions=(asyncio.TimeoutError, ConnectionError),
        )
        async def fetch_data() -> str:
            # May raise retryable exceptions
            return await api.call()
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt >= max_retries:
                        logger.error(
                            "Function %s failed after %d retries: %s",
                            func.__name__,
                            max_retries,
                            e,
                        )
                        raise

                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    logger.warning(
                        "Function %s failed (attempt %d/%d): %s. Retrying in %.1fs...",
                        func.__name__,
                        attempt + 1,
                        max_retries + 1,
                        e,
                        delay,
                    )
                    await asyncio.sleep(delay)

            if last_exception:
                raise last_exception
            return None  # type: ignore[return-value]

        return wrapper  # type: ignore[return-value]

    return decorator
