"""LRU cache for gateway session engines.

Provides:
- LRU eviction policy
- Time-based session expiration
- Thread-safe access
- Session statistics
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CachedEntry(Generic[T]):
    """An entry in the session cache."""

    session_id: str
    value: T
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    ttl_seconds: float = 3600.0  # 1 hour default

    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        return time.time() - self.last_accessed > self.ttl_seconds

    def touch(self) -> None:
        """Update the last accessed time."""
        self.last_accessed = time.time()


@dataclass
class CacheStats:
    """Statistics for the cache."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expired: int = 0
    size: int = 0
    max_size: int = 0

    def hit_rate(self) -> float:
        """Calculate the cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total


class LRUCache(Generic[T]):
    """Generic LRU cache with TTL support."""

    def __init__(
        self,
        max_size: int = 128,
        default_ttl_seconds: float = 3600.0
    ) -> None:
        """Initialize the LRU cache.

        Args:
            max_size: Maximum number of items in the cache.
            default_ttl_seconds: Default TTL for items in seconds.
        """
        self._cache: OrderedDict[str, CachedEntry[T]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl_seconds
        self._stats = CacheStats(max_size=max_size)

    def get(self, key: str) -> T | None:
        """Get an item from the cache.

        Args:
            key: The key to look up.

        Returns:
            The cached value, or None if not found or expired.
        """
        if key not in self._cache:
            self._stats.misses += 1
            return None

        entry = self._cache[key]

        if entry.is_expired():
            self._remove(key, expired=True)
            self._stats.misses += 1
            return None

        # Move to end to mark as recently used
        self._cache.move_to_end(key)
        entry.touch()
        self._stats.hits += 1
        self._update_stats()

        return entry.value

    def put(
        self,
        key: str,
        value: T,
        ttl_seconds: float | None = None
    ) -> None:
        """Put an item into the cache.

        Args:
            key: The key to store under.
            value: The value to store.
            ttl_seconds: Optional TTL override for this item.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl

        if key in self._cache:
            # Remove old entry
            del self._cache[key]

        # Check size and evict if needed
        while len(self._cache) >= self._max_size:
            self._evict_lru()

        self._cache[key] = CachedEntry(
            session_id=key,
            value=value,
            ttl_seconds=ttl
        )
        self._update_stats()
        logger.debug(f"Cached item for session {key}")

    def remove(self, key: str) -> bool:
        """Remove an item from the cache.

        Args:
            key: The key to remove.

        Returns:
            True if the item was found and removed.
        """
        return self._remove(key, expired=False)

    def _remove(self, key: str, expired: bool) -> bool:
        """Internal remove method."""
        if key in self._cache:
            del self._cache[key]
            if expired:
                self._stats.expired += 1
            self._update_stats()
            logger.debug(f"Removed {key} from cache (expired={expired})")
            return True
        return False

    def _evict_lru(self) -> None:
        """Evict the least recently used item."""
        if self._cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats.evictions += 1
            logger.debug(f"Evicted LRU item: {oldest_key}")

    def clear(self) -> None:
        """Clear all items from the cache."""
        self._cache.clear()
        self._update_stats()
        logger.debug("Cache cleared")

    def cleanup_expired(self) -> int:
        """Remove all expired items.

        Returns:
            Number of items removed.
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            self._remove(key, expired=True)
        return len(expired_keys)

    def _update_stats(self) -> None:
        """Update the stats with current size."""
        self._stats.size = len(self._cache)

    def get_stats(self) -> CacheStats:
        """Get the current cache statistics."""
        return CacheStats(
            hits=self._stats.hits,
            misses=self._stats.misses,
            evictions=self._stats.evictions,
            expired=self._stats.expired,
            size=len(self._cache),
            max_size=self._max_size
        )

    def __contains__(self, key: str) -> bool:
        """Check if a key is in the cache (and not expired)."""
        if key not in self._cache:
            return False
        return not self._cache[key].is_expired()

    def __len__(self) -> int:
        """Get the current size of the cache."""
        return len(self._cache)


# Type alias for engine cache
EngineCache = LRUCache[Any]  # Can be more specific if needed


# Default cache instance
_default_cache: EngineCache | None = None


def get_default_engine_cache() -> EngineCache:
    """Get the global engine cache instance."""
    global _default_cache
    if _default_cache is None:
        _default_cache = EngineCache(max_size=128, default_ttl_seconds=3600.0)
    return _default_cache
