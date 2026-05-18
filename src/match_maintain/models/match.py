"""Pydantic 匹配模型。"""
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class MatchResult(str, Enum):
    ATTACKER_WIN = "attacker_win"
    DEFENDER_WIN = "defender_win"


class MatchSource(str, Enum):
    FORUM = "论坛"
    SELF = "自建"
    OTHER = "其他"


class TrustLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MatchEntry(BaseModel):
    """严格模型（用于响应序列化）。"""
    id: str = Field(..., min_length=4, max_length=4, pattern=r"^[0-9]+$")
    defender_team: list[str] = Field(..., min_length=5, max_length=5)
    attacker_team: list[str] = Field(..., min_length=5, max_length=5)
    result: MatchResult
    source: MatchSource
    trust: TrustLevel = TrustLevel.MEDIUM
    custom_def_tag: str = ""
    margin: str = "unknown"
    note: str = ""
    tested: int = 0

    class Config:
        use_enum_values = True


class MatchEntryRaw(BaseModel):
    """灵活模型（保留原始 TOML 结构）。"""
    model_config = {"extra": "allow"}

    id: str
    defender_team: list[str] = []
    attacker_team: list[str] = []
    result: str = ""
    source: str = ""
    trust: str = "medium"
    custom_def_tag: str = ""
    margin: str = "unknown"
    notes: str = ""
    date: str = ""
    uploader_tag: str = "dev"
    defender_burst: dict[str, Any] = Field(default_factory=dict)
    attacker_burst: dict[str, Any] = Field(default_factory=dict)
    tested: int = 0
