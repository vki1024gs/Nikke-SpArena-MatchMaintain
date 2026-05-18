"""Git 历史模型。"""
from datetime import datetime
from pydantic import BaseModel


class GitCommit(BaseModel):
    hash: str
    short_hash: str
    author: str
    email: str
    date: datetime
    message: str


class HistoryResponse(BaseModel):
    commits: list[GitCommit]
    total: int
    has_more: bool = False


class BlameEntry(BaseModel):
    line_number: int
    commit_hash: str
    author: str
    date: datetime
    content: str
