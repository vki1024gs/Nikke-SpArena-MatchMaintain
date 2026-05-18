"""FastAPI 依赖注入。"""
from __future__ import annotations

from contextvars import ContextVar
from functools import lru_cache

from ..config import Settings
from ..core.cache import MemoryCache
from ..domain.fixer_service import FixerService
from ..domain.match_service import MatchService
from ..domain.validate_service import ValidateService
from ..infrastructure.toml_repository import TOMLRepository

_active_file: ContextVar[str | None] = ContextVar("active_file", default=None)


def set_active_file(name: str | None):
    _active_file.set(name)


def _build_repo(settings: Settings | None = None) -> TOMLRepository:
    if settings is None:
        settings = Settings()
    file_name = _active_file.get()
    if not file_name:
        # 默认使用目录下最新的 matches*.toml
        candidates = list(settings.data_dir.glob("matches*.toml"))
        if candidates:
            candidates.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            file_name = candidates[0].name
        elif (settings.data_dir / "matches.toml").exists():
            file_name = "matches.toml"
    if file_name:
        matches_path = settings.data_dir / file_name
    else:
        matches_path = settings.data_dir / "matches.toml"
    return TOMLRepository(matches_path=matches_path, data_dir=settings.data_dir)


def get_repository() -> TOMLRepository:
    return _build_repo()


@lru_cache(maxsize=1)
def get_cache() -> MemoryCache:
    return MemoryCache(default_ttl=Settings().cache_ttl)


def get_match_service() -> MatchService:
    return MatchService(repo=_build_repo(), cache=get_cache())


def get_validate_service() -> ValidateService:
    settings = Settings()
    return ValidateService(repo=_build_repo(settings), data_dir=settings.data_dir)


def get_fixer_service() -> FixerService:
    return FixerService(repo=_build_repo())
