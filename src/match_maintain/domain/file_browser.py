"""数据文件浏览器 — 扫描指定目录下的 TOML 文件。"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class FileInfo(BaseModel):
    name: str
    path: str
    size: int
    modified: str


def scan_toml_files(data_dir: Path) -> list[FileInfo]:
    """扫描目录下所有 .toml 文件（排除 schema）。"""
    files = []
    if not data_dir.exists() or not data_dir.is_dir():
        return files
    for f in sorted(data_dir.iterdir()):
        if f.suffix == ".toml" and f.name != "match_schema.toml":
            s = f.stat()
            files.append(FileInfo(
                name=f.name,
                path=str(f.resolve()),
                size=s.st_size,
                modified=datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M"),
            ))
    return files
