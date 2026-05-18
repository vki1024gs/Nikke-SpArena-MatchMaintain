"""Match CRUD endpoints."""
from fastapi import APIRouter, Depends, Header, Response
from fastapi.responses import JSONResponse

from ...core.dependencies import get_match_service, get_repository
from ...models.request import MatchCreateRequest, MatchUpdateRequest, PreviewResponse

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("")
async def list_matches(page: int = 1, per_page: int = 50, service=Depends(get_match_service)):
    """分页查询对局。"""
    return await service.get_paginated(page=page, per_page=per_page)


@router.get("/{match_id}")
async def get_match(match_id: str, service=Depends(get_match_service)):
    """查询单个对局。"""
    return await service.get_by_id(match_id)


@router.post("")
async def create_match(req: MatchCreateRequest, service=Depends(get_match_service)):
    """新增对局。"""
    data = req.model_dump(exclude={"reason"})
    return await service.create(data)


@router.put("/{match_id}")
async def update_match(match_id: str, req: MatchUpdateRequest, service=Depends(get_match_service)):
    """更新对局。"""
    changes = {k: v for k, v in req.model_dump(exclude={"reason"}).items() if v is not None}
    return await service.update(match_id, changes)


@router.delete("/{match_id}")
async def delete_match(match_id: str, service=Depends(get_match_service)):
    """删除对局。"""
    await service.delete(match_id)
    return {"message": f"Deleted match {match_id}"}


@router.post("/{match_id}/preview", response_model=PreviewResponse)
async def preview_update(match_id: str, req: MatchUpdateRequest, service=Depends(get_match_service)):
    """预览更新（不保存）。"""
    changes = {k: v for k, v in req.model_dump(exclude={"reason"}).items() if v is not None}
    return await service.preview_update(match_id, changes)
