"""Git 版本控制 — 用系统 git 管理 TOML 数据文件版本。"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class GitCommit:
    hash: str
    short_hash: str
    author: str
    email: str
    date: datetime
    message: str


@dataclass
class BlameEntry:
    line_number: int
    commit_hash: str
    author: str
    date: datetime
    content: str


class GitVersioning:
    """data/ 目录的 git 版本控制封装。"""

    def __init__(self, data_dir: Path):
        self._data_dir = data_dir.resolve()

    @property
    def is_initialized(self) -> bool:
        return (self._data_dir / ".git").exists()

    def init_repo(self, matches_file: Path) -> None:
        """初始化 git 仓库并提交初始数据。"""
        if self.is_initialized:
            return
        self._run("init")
        self._run("add", str(matches_file))
        self._run("commit", "-m", "Initial: import match data")

    def commit(self, message: str) -> str:
        """暂存 matches 文件并提交，返回 short hash。"""
        matches = self._data_dir / "matches.toml"
        self._run("add", str(matches))
        result = self._run("commit", "-m", message)
        # 获取最新 commit hash
        short = self._run("rev-parse", "--short", "HEAD").strip()
        return short

    def log(self, limit: int = 50) -> list[GitCommit]:
        """获取提交历史。"""
        fmt = "%H|||%h|||%an|||%ae|||%ai|||%s"
        out = self._run("log", f"--format={fmt}", f"-{limit}", "--")
        if not out.strip():
            return []

        commits = []
        for line in out.strip().split("\n"):
            parts = line.split("|||")
            if len(parts) >= 6:
                commits.append(GitCommit(
                    hash=parts[0],
                    short_hash=parts[1],
                    author=parts[2],
                    email=parts[3],
                    date=datetime.fromisoformat(parts[4].strip()),
                    message=parts[5],
                ))
        return commits

    def show_patch(self, commit_hash: str) -> str:
        """获取提交的 diff。"""
        return self._run("show", "--format=", "--patch", commit_hash)

    def revert(self, commit_hash: str) -> str:
        """回滚到指定提交。"""
        self._run("revert", "--no-edit", commit_hash)
        return self._run("rev-parse", "--short", "HEAD").strip()

    def blame(self) -> list[BlameEntry]:
        """获取当前文件的 blame 信息。"""
        matches = self._data_dir / "matches.toml"
        fmt = "%H%n%an%n%ai"
        out = self._run("blame", f"--line-porcelain", str(matches))
        # Simplified blame parsing
        entries = []
        lines = out.strip().split("\n")
        for line in lines:
            if line.startswith("\t"):
                pass  # content line, skip
        # Use simpler format
        return self._parse_blame_simple()

    def _parse_blame_simple(self) -> list[BlameEntry]:
        out = self._run("blame", "--line-porcelain", str(self._data_dir / "matches.toml"))
        entries = []
        lineno = 0
        current_hash = ""
        current_author = ""
        current_date = ""

        for line in out.strip().split("\n"):
            if line.startswith("boundary"):
                continue
            if line.startswith("commit "):
                current_hash = line[7:14]
            elif line.startswith("author "):
                current_author = line[7:]
            elif line.startswith("author-time "):
                try:
                    current_date = datetime.fromtimestamp(int(line[12:]))
                except (ValueError, OSError):
                    current_date = datetime.now()
            elif line.startswith("\t"):
                lineno += 1
                entries.append(BlameEntry(
                    line_number=lineno,
                    commit_hash=current_hash,
                    author=current_author,
                    date=current_date,
                    content=line[1:],
                ))

        return entries

    def _run(self, *args: str, cwd: Path | None = None) -> str:
        result = subprocess.run(
            ["git", "-C", str(cwd or self._data_dir)] + list(args),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            from ..core.exceptions import GitError
            raise GitError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout
