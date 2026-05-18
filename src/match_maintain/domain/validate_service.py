"""验证业务逻辑服务。"""
from __future__ import annotations

import re
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from ..models.validation import ValidationResult, DeepValidationResult
from ..core.schema import get_schema


class ValidateService:
    def __init__(self, repo, data_dir=None):
        self._repo = repo
        self._data_dir = data_dir

    async def quick_validate(self) -> ValidationResult:
        """快速验证：ID、必填字段、source/trust、队伍人数、角色名。"""
        matches, _ = await self._repo.read_all()
        issues: list[str] = []

        schema = get_schema()
        required = schema.required_fields
        valid_names = await self._load_valid_names()

        prev_id = 0
        for idx, m in enumerate(matches, 1):
            mid = str(m.get("id", ""))

            if not re.match(r"^\d{4}$", mid):
                issues.append(f"#{idx} id 格式错误: '{mid}'（应为4位数字）")
            else:
                curr_id = int(mid)
                if curr_id <= prev_id:
                    issues.append(f"#{idx} id 未递增: {curr_id} <= {prev_id}")
                prev_id = curr_id

            for field in required:
                if field not in m:
                    issues.append(f"#{idx} (id={mid}) 缺少字段: {field}")

            src = m.get("source", "")
            if src not in ["论坛", "自建", "其他"]:
                issues.append(f"#{idx} (id={mid}) source 不合法: '{src}'")

            trust = m.get("trust", "")
            if trust not in ["low", "medium", "high"]:
                issues.append(f"#{idx} (id={mid}) trust 不合法: '{trust}'")

            for side in ["defender_team", "attacker_team"]:
                team = m.get(side, [])
                if not isinstance(team, list):
                    issues.append(f"#{idx} (id={mid}) {side} 不是列表")
                    continue
                if len(team) != 5:
                    issues.append(f"#{idx} (id={mid}) {side} 人数不为5: {len(team)}")
                    continue
                for name in team:
                    if valid_names and name not in valid_names:
                        issues.append(f"#{idx} (id={mid}) {side} 含无效角色: '{name}'")

        return ValidationResult(passed=len(issues) == 0, issues=issues)

    async def deep_validate(self) -> DeepValidationResult:
        """深度验证：字段顺序、类型、合法值、空值。"""
        matches, _ = await self._repo.read_all()
        schema = get_schema()

        field_order = schema.order
        required = schema.required_fields
        non_empty = schema.non_empty_fields
        field_types = {name: f.type for name, f in schema.fields.items()}
        valid_values = {name: f.enum_values for name, f in schema.fields.items() if f.enum_values}
        defaults = {name: f.default for name, f in schema.fields.items() if f.default is not None}

        type_map = {"string": str, "array": list, "int": int, "map": dict, "text": str, "date": str}

        structured_issues = []
        human_report = []
        warnings = []

        for m in matches:
            mid = m.get("id", "?")
            entry_keys = list(m.keys())

            for field in required:
                if field not in m:
                    default = defaults.get(field)
                    structured_issues.append({
                        "id": mid, "type": "missing_field", "field": field,
                        "action": "add_field_with_default", "default": default,
                    })
                    human_report.append(f"[id={mid}] ✗ 缺少必填字段: {field}")

            for k in entry_keys:
                if k not in field_order:
                    structured_issues.append({
                        "id": mid, "type": "extra_field", "field": k, "action": "remove_field",
                    })
                    human_report.append(f"[id={mid}] ✗ 多余字段: {k}")

            ordered_expected = [k for k in field_order if k in entry_keys]
            ordered_actual = [k for k in entry_keys if k in field_order]
            if ordered_expected != ordered_actual:
                structured_issues.append({
                    "id": mid, "type": "wrong_order", "action": "reorder_fields",
                    "expected": ordered_expected, "actual": ordered_actual,
                })
                human_report.append(f"[id={mid}] ✗ 字段顺序错误")

            for field, expected_type_name in field_types.items():
                if field not in m:
                    continue
                expected_type = type_map.get(expected_type_name)
                if expected_type and not isinstance(m[field], expected_type):
                    structured_issues.append({
                        "id": mid, "type": "wrong_type", "field": field, "action": "type_mismatch",
                        "actual_type": type(m[field]).__name__, "expected_type": expected_type_name,
                    })
                    human_report.append(f"[id={mid}] ✗ 字段类型错误: {field}")

            for field, allowed in valid_values.items():
                if field not in m:
                    continue
                val = m[field]
                if val not in allowed:
                    warnings.append({"id": mid, "field": field, "value": val, "allowed": allowed})

            for field in non_empty:
                if field not in m:
                    continue
                val = m[field]
                if isinstance(val, str) and val.strip() == "":
                    structured_issues.append({
                        "id": mid, "type": "empty_field", "field": field, "action": "reject_manual_fix",
                    })
                    human_report.append(f"[id={mid}] ✗ 字段为空: {field}")

        return DeepValidationResult(
            passed=len(structured_issues) == 0,
            human_report=human_report,
            structured_issues=structured_issues,
            warnings=warnings,
        )

    async def _load_valid_names(self) -> set[str]:
        if self._data_dir is None:
            return set()

        candidates = [
            self._data_dir / "references" / "chara_list_pvp.toml",
            self._data_dir / "chara_list_pvp.toml",
        ]

        for chara_path in candidates:
            if chara_path.exists():
                with open(chara_path, "rb") as f:
                    data = tomllib.load(f)
                return {c["name"] for c in data.get("characters", [])}

        return set()
