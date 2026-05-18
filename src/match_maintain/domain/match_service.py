"""MatchService — CRUD + 缓存 + 预览。"""
from __future__ import annotations

from ..core.cache import MemoryCache
from ..domain.field_completer import complete_match
from ..domain.transaction import TransactionInterceptor
from ..infrastructure.toml_repository import TOMLRepository


class MatchService:
    def __init__(self, repo: TOMLRepository, cache: MemoryCache):
        self._repo = repo
        self._cache = cache

    async def get_paginated(self, page: int = 1, per_page: int = 20) -> dict:
        """分页查询。"""
        file_key = self._repo._matches_path.name
        cache_key = f"matches:{file_key}:page:{page}:{per_page}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached

        matches, file_hash = await self._repo.read_all()
        total = len(matches)
        total_pages = max(1, (total + per_page - 1) // per_page)
        start = (page - 1) * per_page
        end = start + per_page
        page_matches = matches[start:end]

        result = {
            "matches": page_matches,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        }
        await self._cache.set(cache_key, result, ttl=60)
        return result

    async def get_by_id(self, match_id: str) -> dict:
        """按 ID 查询。"""
        file_key = self._repo._matches_path.name
        cache_key = f"matches:{file_key}:id:{match_id}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached

        entry, _ = await self._repo.read_by_id(match_id)
        await self._cache.set(cache_key, entry, ttl=300)
        return entry

    async def get_stats(self, archive_count: int = 0, backup_count: int = 0) -> dict:
        """仪表盘统计。"""
        matches, _ = await self._repo.read_all()
        source_dist: dict[str, int] = {}
        for m in matches:
            src = m.get("source", "未知")
            source_dist[src] = source_dist.get(src, 0) + 1

        return {
            "total_matches": len(matches),
            "archive_count": archive_count,
            "backup_count": backup_count,
            "source_distribution": source_dist,
        }

    async def create(self, match_data: dict) -> dict:
        """新增对局。"""
        complete = complete_match(**match_data)
        self._repo.create(complete, f"create match {match_data.get('id', 'unknown')}")
        await self.invalidate_cache()
        return complete

    async def update(self, match_id: str, changes: dict) -> dict:
        """更新对局。"""
        result = await self._repo.update(match_id, changes)
        await self.invalidate_cache()
        return result

    async def delete(self, match_id: str) -> None:
        """删除对局。"""
        await self._repo.delete(match_id)
        await self.invalidate_cache()

    async def preview_update(self, match_id: str, changes: dict) -> dict:
        """预览更新（不保存）。"""
        try:
            current, _ = await self._repo.read_by_id(match_id)
        except Exception:
            current = {"id": match_id}

        tx = TransactionInterceptor(current)
        tx.apply_changes(**{k: v for k, v in changes.items() if v is not None})
        valid, errors = tx.validate()

        return {
            "diff_text": tx.get_diff_text(),
            "valid": valid,
            "errors": errors,
            "proposed": tx.get_proposed(),
        }

    async def invalidate_cache(self) -> None:
        await self._cache.clear("matches:*")
