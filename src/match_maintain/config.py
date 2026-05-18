"""应用配置 — Pydantic Settings，支持环境变量覆盖。"""
from __future__ import annotations

from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，优先级：环境变量 > .env > 默认值。"""
    model_config = SettingsConfigDict(
        env_prefix="MATCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    app_name: str = "Match Maintenance"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # 服务器
    host: str = "0.0.0.0"
    port: int = 2771
    reload: bool = False

    # 数据路径
    data_dir: Path = Path("/Users/starai/.hermes/skills/nikke-pvp/data")
    matches_file: str = ""
    schema_file: str = "match_schema.toml"

    # 缓存
    cache_ttl: int = 300  # 秒

    # 日志
    log_level: str = "INFO"
    log_format: str = "text"  # text | json

    # 分页
    page_size: int = 50

    # Git
    git_author_name: str = "match-maintain"
    git_author_email: str = "tool@local"

    @property
    def matches_path(self) -> Path:
        return self.data_dir / self.matches_file

    @property
    def schema_path(self) -> Path:
        return self.data_dir / self.schema_file


@lru_cache
def get_settings() -> Settings:
    return Settings()
