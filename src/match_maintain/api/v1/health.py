"""Health check endpoint."""
from datetime import datetime
from fastapi import APIRouter

from ...config import get_settings

router = APIRouter()


@router.get("/health")
async def health():
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "0.2.0",
        "data_dir": str(settings.data_dir.resolve()),
        "matches_file": settings.matches_file,
        "timestamp": datetime.now().isoformat(),
    }
