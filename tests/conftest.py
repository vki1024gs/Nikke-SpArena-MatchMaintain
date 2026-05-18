"""测试夹具"""
from __future__ import annotations

from pathlib import Path
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient

from src.app.config import Settings
from src.app.factory import create_app


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """创建测试用配置。"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    return Settings(
        data_dir=data_dir,
        matches_file="test_matches.toml",
        schema_file="test_schema.toml",
    )


@pytest.fixture
def app(test_settings: Settings):
    """创建测试用 FastAPI 应用。"""
    return create_app(test_settings)


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """创建异步 HTTP 客户端。"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
