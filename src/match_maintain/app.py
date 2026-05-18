"""应用工厂 — 创建和配置 FastAPI 应用。"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import Settings
from .core.logging import setup_logging
from .middleware.error_handler import register_exception_handlers
from .middleware.request_logging import RequestLoggingMiddleware
from .api.v1 import router as api_v1_router


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        from .config import get_settings
        settings = get_settings()

    setup_logging(level=settings.log_level, log_format=settings.log_format)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from loguru import logger
        logger.info(f"Starting {settings.app_name} v0.2.0")
        logger.info(f"Data directory: {settings.data_dir.resolve()}")
        yield
        logger.info("Shutting down")

    app = FastAPI(
        title=settings.app_name,
        description="NIKKE PVP 对局数据维护工具",
        version="0.2.0",
        lifespan=lifespan,
        debug=settings.debug,
    )

    app.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(app)

    app.include_router(api_v1_router)

    # 静态文件
    static_dir = Path(__file__).parent / "web" / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Web 路由
    from .web.routes import register_web_routes
    register_web_routes(app, settings)

    return app
