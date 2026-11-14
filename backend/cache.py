"""Bounded in-memory cache for successful sentence API responses."""

from collections import OrderedDict
from threading import Lock
from typing import Any

CacheKey = tuple[tuple[str, ...], str]


class ResponseCache:
    """Thread-safe least-recently-used cache with a fixed maximum size."""

    def __init__(self, max_entries: int = 256) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be greater than zero")
        self._max_entries = max_entries
        self._entries: OrderedDict[CacheKey, dict[str, Any]] = OrderedDict()
        self._lock = Lock()

    def get(self, key: CacheKey) -> dict[str, Any] | None:
        """Return a shallow copy of a cached response and mark it recently used."""
        with self._lock:
            response = self._entries.get(key)
            if response is None:
                return None
            self._entries.move_to_end(key)
            return response.copy()

    def put(self, key: CacheKey, response: dict[str, Any]) -> None:
        """Store a successful response and evict least-recently-used entries."""
        with self._lock:
            self._entries[key] = response.copy()
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        """Remove all cached responses."""
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)
