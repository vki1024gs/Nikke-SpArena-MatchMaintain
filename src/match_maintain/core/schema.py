"""Schema 加载器 — 从 TOML 读取字段规则。"""
from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class FieldSchema:
    """单个字段的元数据定义"""
    def __init__(self, name: str, definition: Dict[str, Any]):
        self.name = name
        self.type: str = definition.get("type", "string")
        self.required: bool = definition.get("required", False)
        self.non_empty: bool = definition.get("non_empty", False)
        self.default: Any = definition.get("default")
        self.enum_values: List[str] = definition.get("enum_values", [])
        self.max_length: int = definition.get("max_length")
        self.format: Optional[str] = definition.get("format")
        self.order: int = definition.get("order", 0)


class Schema:
    """对局数据 Schema，所有规则从 TOML 读取，禁止硬编码。"""

    def __init__(self, schema_path: Path | None = None):
        if schema_path is None:
            schema_path = _find_default_schema()

        with open(schema_path, "rb") as f:
            data = tomllib.load(f)

        self.fields: Dict[str, FieldSchema] = {}
        raw_fields = data.get("fields", {})

        for name, defn in sorted(raw_fields.items(), key=lambda item: item[1].get("order", 0)):
            self.fields[name] = FieldSchema(name, defn)

        self.order: list[str] = [f.name for f in self.fields.values()]
        self.required_fields = [n for n, f in self.fields.items() if f.required]
        self.non_empty_fields = [n for n, f in self.fields.items() if f.non_empty]

    def get_field(self, name: str) -> FieldSchema | None:
        return self.fields.get(name)

    def get_valid_values(self, field: str) -> list | None:
        f = self.fields.get(field)
        return f.enum_values if f else None

    def get_default(self, field: str) -> Any:
        f = self.fields.get(field)
        return f.default if f else None


def _find_default_schema() -> str:
    _project_root = Path(__file__).parent.parent.parent
    # 优先从 config/ 读取（项目级模板，纳入 git 管理）
    config_path = _project_root / "config" / "match_schema.toml"
    if config_path.exists():
        return str(config_path)
    # 兼容旧路径
    for root in [_project_root / "data", _project_root.parent / "data"]:
        p = root / "match_schema.toml"
        if p.exists():
            return str(p)
    return "config/match_schema.toml"


def get_schema_path() -> str:
    env_path = os.environ.get("MATCH_SCHEMA_PATH")
    if env_path and Path(env_path).exists():
        return env_path
    return _find_default_schema()


def set_schema_path(path: str) -> None:
    os.environ["MATCH_SCHEMA_PATH"] = path
    reload_schema()


@lru_cache(maxsize=1)
def get_schema() -> Schema:
    return Schema(Path(get_schema_path()))


def reload_schema() -> None:
    get_schema.cache_clear()
    get_schema()
