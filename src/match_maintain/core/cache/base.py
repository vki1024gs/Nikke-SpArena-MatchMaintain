"""缓存基类。"""
from abc import ABC, abstractmethod
from typing import Any


class BaseCache(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None: ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def clear(self, pattern: str | None = None) -> None: ...
