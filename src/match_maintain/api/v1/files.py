"""文件浏览器 API。"""
from fastapi import APIRouter

from ...config import get_settings
from ...domain.file_browser import scan_toml_files

router = APIRouter(prefix="/files", tags=["files"])


@router.get("")
async def list_files():
    """列出默认目录下的 TOML 数据文件。"""
    settings = get_settings()
    return {"files": [f.model_dump() for f in scan_toml_files(settings.data_dir)]}
