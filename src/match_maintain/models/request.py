"""请求/响应模型。"""
from typing import Any, Optional
from pydantic import BaseModel, Field


class MatchCreateRequest(BaseModel):
    """新增对局请求。"""
    id: str
    defender_team: list[str]
    attacker_team: list[str]
    result: str
    source: str = "论坛"
    date: str = ""
    margin: Optional[str] = None
    trust: Optional[str] = None
    custom_def_tag: str = ""
    notes: str = ""
    defender_burst: dict[str, Any] = Field(default_factory=dict)
    attacker_burst: dict[str, Any] = Field(default_factory=dict)
    uploader_tag: str = "dev"
    reason: str = ""  # git commit message


class MatchUpdateRequest(BaseModel):
    """更新对局请求。"""
    defender_team: Optional[list[str]] = None
    attacker_team: Optional[list[str]] = None
    result: Optional[str] = None
    source: Optional[str] = None
    date: Optional[str] = None
    margin: Optional[str] = None
    trust: Optional[str] = None
    custom_def_tag: Optional[str] = None
    uploader_tag: Optional[str] = None
    notes: Optional[str] = None
    defender_burst: Optional[dict[str, Any]] = None
    attacker_burst: Optional[dict[str, Any]] = None
    reason: str = ""


class PreviewResponse(BaseModel):
    """预览响应。"""
    diff_text: str
    valid: bool
    errors: list[str]
    proposed: dict[str, Any]


class DashboardStats(BaseModel):
    total_matches: int
    archive_count: int
    backup_count: int
    source_distribution: dict[str, int]


class PaginatedMatches(BaseModel):
    matches: list[dict[str, Any]]
    page: int
    per_page: int
    total: int
    total_pages: int


class ArchiveInfo(BaseModel):
    name: str
    size: int
    modified: str
