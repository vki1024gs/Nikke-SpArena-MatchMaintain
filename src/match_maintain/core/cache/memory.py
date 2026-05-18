"""内存缓存 — 带 TTL 和模式清除。"""
import asyncio
import time
import fnmatch
from typing import Any


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expires_at = time.monotonic() + ttl if ttl > 0 else None

    @property
    def expired(self) -> bool:
        return self.expires_at is not None and time.monotonic() > self.expires_at


class MemoryCache:
    """线程安全的内存缓存，支持 TTL 和模式清除。"""

    def __init__(self, default_ttl: int = 300):
        self._cache: dict[str, _CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._default_ttl = default_ttl

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None or entry.expired:
                if entry and entry.expired:
                    del self._cache[key]
                return None
            return entry.value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        async with self._lock:
            self._cache[key] = _CacheEntry(value, ttl or self._default_ttl)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self, pattern: str | None = None) -> None:
        async with self._lock:
            if pattern is None:
                self._cache.clear()
            else:
                keys = [k for k in self._cache if fnmatch.fnmatch(k, pattern)]
                for k in keys:
                    del self._cache[k]
