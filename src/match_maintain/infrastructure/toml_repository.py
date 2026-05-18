"""统一 TOML 数据仓库 — 读写 + git 版本控制。"""
from __future__ import annotations

import asyncio
import copy
import hashlib
import sys
import tempfile
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomlkit

from ..core.exceptions import DataFileError, MatchNotFoundError, ConcurrencyError
from .git_versioning import GitVersioning


class TOMLRepository:
    """TOML 数据仓库，所有读写都经过这里，写入自动 git commit。"""

    def __init__(self, matches_path: Path, data_dir: Path):
        self._matches_path = matches_path.resolve()
        self._data_dir = data_dir.resolve()
        self._lock = asyncio.Lock()
        self._git = GitVersioning(data_dir)

    async def read_all(self) -> tuple[list[dict], str]:
        """读取所有对局，返回列表和文件 hash。"""
        async with self._lock:
            return await self._read_matches()

    async def read_tomlkit_document(self) -> tuple[tomlkit.TOMLDocument, str]:
        """读取原始 tomlkit 文档（保留格式/注释），用于修复等需要格式感知的操作。"""
        async with self._lock:
            content = self._matches_path.read_bytes()
            file_hash = hashlib.sha256(content).hexdigest()
            doc = tomlkit.loads(content.decode("utf-8"))
            return doc, file_hash

    async def read_by_id(self, match_id: str) -> tuple[dict, str]:
        """按 ID 读取单条对局。"""
        data, file_hash = await self.read_all()
        for entry in data:
            if str(entry.get("id")) == match_id:
                return entry, file_hash
        raise MatchNotFoundError(match_id)

    async def write(self, data: list[dict], commit_message: str) -> str:
        """原子写入 TOML + git commit，返回 commit short_hash。"""
        async with self._lock:
            doc = tomlkit.document()
            doc.add(tomlkit.comment("NIKKE PVP match data — managed by match-maintain"))
            doc.add("match", data)
            return await self._write_doc(doc, commit_message)

    async def create(self, match_data: dict, commit_message: str | None = None) -> dict:
        """新增一条对局。"""
        data, _ = await self.read_all()
        data.append(match_data)
        msg = commit_message or f"create match {match_data.get('id', 'unknown')}"
        await self.write(data, msg)
        return match_data

    async def update(self, match_id: str, changes: dict, commit_message: str | None = None) -> dict:
        """更新一条对局。"""
        data, _ = await self.read_all()
        found = None
        for entry in data:
            if str(entry.get("id")) == match_id:
                found = entry
                break
        if found is None:
            raise MatchNotFoundError(match_id)

        changes_display = []
        for key, value in changes.items():
            if key in found and found[key] != value:
                changes_display.append(f"{key}: {found[key]!r} → {value!r}")
            found[key] = value

        msg = commit_message or f"update match {match_id}: {', '.join(changes_display[:3])}"
        await self.write(data, msg)
        return found

    async def delete(self, match_id: str) -> None:
        """删除一条对局。"""
        data, _ = await self.read_all()
        new_data = [e for e in data if str(e.get("id")) != match_id]
        if len(new_data) == len(data):
            raise MatchNotFoundError(match_id)
        await self.write(new_data, f"delete match {match_id}")

    def get_current_hash(self) -> str:
        """获取当前文件 SHA-256。"""
        if not self._matches_path.exists():
            return ""
        return hashlib.sha256(self._matches_path.read_bytes()).hexdigest()

    def git_init(self) -> None:
        """初始化 git 仓库。"""
        self._git.init_repo(self._matches_path)

    def git_log(self, limit: int = 50):
        return self._git.log(limit)

    def git_revert(self, commit_hash: str) -> str:
        return self._git.revert(commit_hash)

    def git_blame(self):
        return self._git.blame()

    def git_show_patch(self, commit_hash: str) -> str:
        return self._git.show_patch(commit_hash)

    @property
    def is_git_initialized(self) -> bool:
        return self._git.is_initialized

    # --- Internal ---

    async def _read_matches(self) -> tuple[list[dict], str]:
        if not self._matches_path.exists():
            raise DataFileError(f"Data file not found: {self._matches_path}")

        content = self._matches_path.read_bytes()
        file_hash = hashlib.sha256(content).hexdigest()

        try:
            data = tomllib.loads(content.decode("utf-8"))
        except Exception as e:
            raise DataFileError(f"Failed to parse TOML: {e}")

        matches = data.get("match", [])
        return matches, file_hash

    async def _write_doc(self, doc: tomlkit.TOMLDocument, commit_message: str) -> str:
        self._ensure_inline_maps(doc)

        # Atomic write: temp file → rename
        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            dir=self._data_dir,
            suffix=".toml.tmp",
            delete=False,
            encoding="utf-8",
        )
        try:
            tmp.write(tomlkit.dumps(doc))
            tmp.flush()
            tmp.close()
            Path(tmp.name).rename(self._matches_path)
        except Exception:
            tmp.close()
            try:
                Path(tmp.name).unlink()
            except OSError:
                pass
            raise

        # Git commit
        if self._git.is_initialized:
            self._git.commit(commit_message)

        return commit_message

    def _ensure_inline_maps(self, doc: tomlkit.TOMLDocument) -> None:
        """将所有 match 表中的 dict 值转为 inline table，避免多行子表。"""
        matches_table = doc.get("match", [])
        for item in matches_table:
            self._convert_table_dicts(item)

    def _convert_table_dicts(self, obj):
        if isinstance(obj, dict):
            for key in list(obj.keys()):
                val = obj[key]
                if isinstance(val, dict) and not isinstance(val, tomlkit.items.InlineTable):
                    it = tomlkit.inline_table()
                    for k, v in val.items():
                        it[k] = v
                    obj[key] = it
                    self._convert_table_dicts(obj[key])
                elif isinstance(val, list):
                    for item in val:
                        self._convert_table_dicts(item)
