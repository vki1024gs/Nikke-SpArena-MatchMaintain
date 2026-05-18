"""字段补全 — 根据 schema 默认值填充缺失字段。"""
from __future__ import annotations

from ..core.schema import get_schema


def complete_fields(data: dict) -> dict:
    """填充缺失字段为 schema 默认值。"""
    schema = get_schema()
    result = dict(data)

    for name, field in schema.fields.items():
        if name not in result or result[name] is None:
            if field.default is not None:
                result[name] = field.default
            elif field.type == "array":
                result[name] = []
            elif field.type == "map":
                result[name] = {}
            elif field.type in ("string", "text"):
                result[name] = ""

    return result


def complete_match(**kwargs) -> dict:
    """补全单条对局数据。"""
    return complete_fields(kwargs)
