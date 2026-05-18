"""纯领域事务拦截器 — diff 计算、校验、预览，无 ORM 依赖。"""
from __future__ import annotations

import copy
import re
from typing import Any

from ..core.schema import get_schema, Schema


class TransactionInterceptor:
    """计算变更 diff、校验 schema、生成预览文本。"""

    def __init__(self, current_data: dict):
        self.current = copy.deepcopy(current_data)
        self.proposed = copy.deepcopy(current_data)
        self.diff: dict[str, Any] = {}
        self.errors: list[str] = []
        self._schema: Schema = get_schema()

    def apply_changes(self, **kwargs) -> None:
        """应用非 None 变更，计算 diff，自动补全字段。"""
        changed = False
        for key, value in kwargs.items():
            if value is not None and value != self.current.get(key):
                self.proposed[key] = value
                self.diff[key] = {"old": self.current.get(key), "new": value}
                changed = True

        if changed:
            from .field_completer import complete_fields
            self.proposed = complete_fields(self.proposed)

    def validate(self) -> tuple[bool, list[str]]:
        """校验 proposed 数据。"""
        errors = []

        # 必填字段
        for name in self._schema.required_fields:
            if name not in self.proposed or self.proposed[name] in (None, "", []):
                errors.append(f"字段 '{name}' 为必填")

        # 非空字段
        for name in self._schema.non_empty_fields:
            val = self.proposed.get(name)
            if val is not None and isinstance(val, str) and val.strip() == "":
                errors.append(f"字段 '{name}' 不能为空")

        # 枚举值
        for name in self.proposed:
            valid = self._schema.get_valid_values(name)
            if valid and self.proposed[name] not in valid:
                errors.append(f"字段 '{name}' 值 '{self.proposed[name]}' 不在允许值 {valid} 中")

        # 类型检查
        for name in self.proposed:
            field = self._schema.get_field(name)
            if field is None:
                continue
            if field.type == "array" and not isinstance(self.proposed[name], (list, tuple)):
                errors.append(f"字段 '{name}' 应为数组")
            elif field.type in ("string", "text", "date", "enum") and not isinstance(self.proposed[name], str):
                errors.append(f"字段 '{name}' 应为字符串")

        # 日期格式
        date_field = self._schema.get_field("date")
        if date_field and date_field.format:
            val = self.proposed.get("date", "")
            if val and not re.match(r"^\d{4}-\d{2}-\d{2}$", val):
                errors.append(f"日期格式应为 YYYY-MM-DD，当前: {val}")

        self.errors = errors
        return (len(errors) == 0, errors)

    def get_diff_text(self) -> str:
        """人类可读 diff。"""
        if not self.diff:
            return "无变更"

        lines = []
        for name in self._schema.order:
            if name not in self.diff:
                continue
            d = self.diff[name]
            old = _format_value(d["old"])
            new = _format_value(d["new"])
            lines.append(f"  {name}: {old!r} → {new!r}")

        return "\n".join(lines)

    def get_proposed(self) -> dict:
        return dict(self.proposed)


def _format_value(val: Any) -> str:
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    return str(val) if val is not None else "None"
