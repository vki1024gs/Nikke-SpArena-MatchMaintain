"""SDK 异常类"""


class MatchSDKError(Exception):
    """SDK 基础异常"""


class ConnectionError(MatchSDKError):
    """连接失败"""


class MatchNotFoundError(MatchSDKError):
    """对局不存在"""


class ValidationError(MatchSDKError):
    """验证失败"""
    def __init__(self, message: str, issues: list = None):
        self.issues = issues or []
        super().__init__(message)


class FixError(MatchSDKError):
    """修复失败"""
