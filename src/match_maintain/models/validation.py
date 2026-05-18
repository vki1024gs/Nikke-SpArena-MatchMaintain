"""验证结果模型。"""
from pydantic import BaseModel, Field
from typing import Any


class ValidationIssue(BaseModel):
    match_id: str = ""
    field: str = ""
    issue_type: str = ""
    message: str = ""
    action: str = ""  # remove_field, add_field_with_default, reorder_fields
    fix_value: Any = None


class ValidationResult(BaseModel):
    passed: bool
    issues: list[str] = []
    warnings: list[str] = []

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


class DeepValidationResult(BaseModel):
    passed: bool
    human_report: str = ""
    structured_issues: list[ValidationIssue] = []
    warnings: list[str] = []


class FixResult(BaseModel):
    fixed_count: int
    backup_path: str = ""
    message: str = ""
