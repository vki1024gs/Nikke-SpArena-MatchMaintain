"""Match Client — Agent 交互的核心 SDK。"""
from __future__ import annotations

from typing import Optional

import httpx

from .exceptions import MatchSDKError, ConnectionError, MatchNotFoundError, ValidationError, FixError


class MatchClient:
    """对局维护 SDK — Agent 使用的主要入口。

    用法：
        >>> from sdk import MatchClient
        >>> client = MatchClient("http://localhost:2771")
        >>> client.health()
        >>> client.quick_validate()
        >>> client.fix()
    """

    def __init__(self, base_url: str = "http://localhost:2771", timeout: int = 30):
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self._client.close()

    def _request(self, method: str, path: str, **kwargs) -> dict:
        try:
            resp = self._client.request(method, path, **kwargs)
            if resp.status_code == 404:
                detail = resp.json().get("error", resp.json().get("detail", "Not found"))
                raise MatchNotFoundError(detail)
            if resp.status_code == 422:
                data = resp.json()
                raise ValidationError(data.get("error", "Validation failed"), data.get("issues", []))
            if resp.status_code >= 400:
                data = resp.json()
                raise MatchSDKError(data.get("error", data.get("detail", "Unknown error")))
            return resp.json()
        except httpx.ConnectError as e:
            raise ConnectionError(f"无法连接到 {self._base_url}: {e}") from e
        except MatchSDKError:
            raise
        except Exception as e:
            raise MatchSDKError(f"请求失败: {e}") from e

    # ─── Health ───

    def health(self) -> dict:
        return self._request("GET", "/api/v1/health")

    # ─── Matches CRUD ───

    def get_match(self, match_id: str) -> dict:
        return self._request("GET", f"/api/v1/matches/{match_id}")

    def list_matches(self, page: int = 1, per_page: int = 20) -> dict:
        return self._request("GET", "/api/v1/matches", params={"page": page, "per_page": per_page})

    def list_all_matches(self) -> list[dict]:
        all_matches = []
        page = 1
        while True:
            result = self.list_matches(page=page, per_page=100)
            all_matches.extend(result.get("matches", []))
            if page >= result.get("total_pages", 1):
                break
            page += 1
        return all_matches

    def create_match(self, match_data: dict, reason: str = "") -> dict:
        """新增对局。"""
        body = {**match_data, "reason": reason}
        return self._request("POST", "/api/v1/matches", json=body)

    def update_match(self, match_id: str, changes: dict, reason: str = "") -> dict:
        """更新对局。"""
        body = {**changes, "reason": reason}
        return self._request("PUT", f"/api/v1/matches/{match_id}", json=body)

    def delete_match(self, match_id: str) -> dict:
        """删除对局。"""
        return self._request("DELETE", f"/api/v1/matches/{match_id}")

    def preview_update(self, match_id: str, changes: dict) -> dict:
        """预览更新（不保存）。"""
        return self._request("POST", f"/api/v1/matches/{match_id}/preview", json=changes)

    # ─── Validation ───

    def quick_validate(self) -> dict:
        return self._request("POST", "/api/v1/validate/quick")

    def deep_validate(self) -> dict:
        return self._request("POST", "/api/v1/validate/deep")

    def fix(self) -> dict:
        return self._request("POST", "/api/v1/validate/fix")

    # ─── History ───

    def get_history(self, limit: int = 50) -> dict:
        """获取 Git 提交历史。"""
        return self._request("GET", f"/api/v1/history?limit={limit}")

    def get_commit(self, commit_hash: str) -> dict:
        """获取单个提交的 diff。"""
        return self._request("GET", f"/api/v1/history/{commit_hash}")

    def revert_commit(self, commit_hash: str) -> dict:
        """回滚到指定提交。"""
        return self._request("POST", f"/api/v1/history/revert?commit_hash={commit_hash}")

    def get_blame(self) -> dict:
        """获取 blame 信息。"""
        return self._request("GET", "/api/v1/history/blame")

    # ─── 组合操作 ───

    def validate_and_fix(self) -> dict:
        result = self.deep_validate()
        if result.get("passed", True):
            return {"fixed_count": 0, "message": "数据已合规，无需修复"}
        return self.fix()

    def full_maintenance(self) -> dict:
        validation = self.deep_validate()
        fix_result = self.fix() if not validation.get("passed", True) else {"fixed_count": 0, "message": "无需修复"}
        return {
            "validation_passed": validation.get("passed", False),
            "fix_count": fix_result.get("fixed_count", 0),
        }
