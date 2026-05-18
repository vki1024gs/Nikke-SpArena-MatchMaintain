from fastapi import APIRouter

from .health import router as health_router
from .matches import router as matches_router
from .validate import router as validate_router
from .history import router as history_router
from .files import router as files_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(matches_router)
router.include_router(validate_router)
router.include_router(history_router)
router.include_router(files_router)
