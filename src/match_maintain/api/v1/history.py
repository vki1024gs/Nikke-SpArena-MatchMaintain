"""Git history endpoints."""
from fastapi import APIRouter, Depends

from ...models.history import HistoryResponse, GitCommit
from ...core.dependencies import get_repository

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
async def get_history(limit: int = 50, repo=Depends(get_repository)):
    """获取提交历史。"""
    if not repo.is_git_initialized:
        return {"commits": [], "total": 0, "has_more": False, "message": "Git not initialized"}

    commits = repo.git_log(limit)
    return {
        "commits": [
            {
                "hash": c.hash,
                "short_hash": c.short_hash,
                "author": c.author,
                "email": c.email,
                "date": c.date.isoformat(),
                "message": c.message,
            }
            for c in commits
        ],
        "total": len(commits),
        "has_more": len(commits) == limit,
    }


@router.get("/{commit_hash}")
async def get_commit(commit_hash: str, repo=Depends(get_repository)):
    """获取单个提交的 diff。"""
    if not repo.is_git_initialized:
        return {"error": "Git not initialized"}

    patch = repo.git_show_patch(commit_hash)
    return {"hash": commit_hash, "patch": patch}


@router.post("/revert")
async def revert_commit(commit_hash: str, repo=Depends(get_repository)):
    """回滚到指定提交。"""
    if not repo.is_git_initialized:
        return {"error": "Git not initialized"}

    new_hash = repo.git_revert(commit_hash)
    return {"message": f"Reverted to {new_hash}", "new_hash": new_hash}


@router.get("/blame")
async def get_blame(repo=Depends(get_repository)):
    """获取 blame 信息。"""
    if not repo.is_git_initialized:
        return {"entries": []}

    entries = repo.git_blame()
    return {
        "entries": [
            {
                "line_number": e.line_number,
                "commit_hash": e.commit_hash,
                "author": e.author,
                "date": e.date.isoformat(),
                "content": e.content,
            }
            for e in entries
        ]
    }
