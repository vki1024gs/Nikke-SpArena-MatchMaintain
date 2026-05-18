"""Validation endpoints."""
from fastapi import APIRouter, Depends

from ...core.dependencies import get_validate_service, get_fixer_service

router = APIRouter(prefix="/validate", tags=["validate"])


@router.post("/quick")
async def quick_validate(service=Depends(get_validate_service)):
    """快速验证。"""
    return await service.quick_validate()


@router.post("/deep")
async def deep_validate(service=Depends(get_validate_service)):
    """深度验证。"""
    return await service.deep_validate()


@router.post("/fix")
async def fix(service=Depends(get_fixer_service), validate_service=Depends(get_validate_service)):
    """自动修复。"""
    result = await validate_service.deep_validate()
    if result.passed:
        return {"fixed_count": 0, "message": "无需修复"}
    return await service.apply_fixes(result.structured_issues)
