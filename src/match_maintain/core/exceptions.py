"""应用异常定义。"""


class AppError(Exception):
    status_code: int = 500
    detail: str = "Internal server error"


class ConfigError(AppError):
    status_code = 500
    detail = "Configuration error"


class DataFileError(AppError):
    status_code = 500
    detail = "Data file error"


class ValidationError(AppError):
    status_code = 422
    detail = "Validation failed"

    def __init__(self, issues: list[str] | None = None, warnings: list[str] | None = None):
        self.issues = issues or []
        self.warnings = warnings or []
        super().__init__()


class MatchNotFoundError(AppError):
    status_code = 404
    detail = "Match not found"

    def __init__(self, match_id: str):
        self.match_id = match_id
        self.detail = f"Match not found: {match_id}"
        super().__init__()


class FixError(AppError):
    status_code = 500
    detail = "Fix failed"


class CacheError(AppError):
    status_code = 500
    detail = "Cache error"


class ConcurrencyError(AppError):
    status_code = 412
    detail = "Precondition failed: data was modified by another process"


class GitError(AppError):
    status_code = 500
    detail = "Git operation failed"

    def __init__(self, message: str):
        self.detail = f"Git error: {message}"
        super().__init__()
