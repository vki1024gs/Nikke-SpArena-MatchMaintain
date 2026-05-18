"""自动修复服务。"""
from __future__ import annotations

import tomlkit

from ..core.schema import get_schema
from ..models.validation import FixResult


class FixerService:
    def __init__(self, repo):
        self._repo = repo

    async def apply_fixes(self, issues: list[dict]) -> FixResult:
        if not issues:
            return FixResult(fixed_count=0, message="无需修复")

        by_id: dict[str, list[dict]] = {}
        for issue in issues:
            mid = str(issue.get("id", ""))
            by_id.setdefault(mid, []).append(issue)

        # Read raw tomlkit document via public API
        doc, _ = await self._repo.read_tomlkit_document()
        matches = doc.get("match", [])

        fixed_count = 0
        schema = get_schema()
        field_order = schema.order

        for i, m in enumerate(matches):
            mid = str(m.get("id", ""))
            if mid not in by_id:
                continue

            for issue in by_id[mid]:
                action = issue.get("action", "")

                if action == "remove_field":
                    field = issue.get("field")
                    if field and field in m:
                        del m[field]
                        fixed_count += 1

                elif action == "add_field_with_default":
                    field = issue.get("field")
                    if field:
                        default = issue.get("default", "")
                        m[field] = default
                        fixed_count += 1

                elif action == "reorder_fields":
                    expected = issue.get("expected", field_order)
                    _reorder_table(m, expected)
                    fixed_count += 1

        # Write via repository (which handles atomic write + git commit)
        # Convert back to list of dicts for writing
        flat_matches = [dict(m) for m in matches]
        await self._repo.write(flat_matches, "fix: auto-repaired validation issues")

        return FixResult(fixed_count=fixed_count, message=f"已修复 {fixed_count} 处")


def _reorder_table(table: tomlkit.Table, order: list[str]) -> None:
    """重排 table 字段顺序，dict 类型转为内联表。"""
    values = {}
    for k in order:
        if k in table:
            val = table[k]
            if isinstance(val, dict) and not isinstance(val, tomlkit.items.InlineTable):
                it = tomlkit.inline_table()
                for dk, dv in val.items():
                    it[dk] = dv
                values[k] = it
            else:
                values[k] = val

    for k in table:
        if k not in order:
            val = table[k]
            if isinstance(val, dict) and not isinstance(val, tomlkit.items.InlineTable):
                it = tomlkit.inline_table()
                for dk, dv in val.items():
                    it[dk] = dv
                values[k] = it
            else:
                values[k] = val

    table.clear()
    for k in order:
        if k in values:
            table[k] = values[k]
    for k in values:
        if k not in order:
            table[k] = values[k]
