"""异常处理中间件。"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..core.exceptions import (
    AppError, MatchNotFoundError, ValidationError,
    DataFileError, FixError, ConfigError, ConcurrencyError, GitError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(MatchNotFoundError)
    async def handle_not_found(request: Request, exc: MatchNotFoundError):
        return JSONResponse(status_code=404, content={"error": exc.detail})

    @app.exception_handler(ValidationError)
    async def handle_validation(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={
            "error": exc.detail,
            "issues": exc.issues,
            "warnings": exc.warnings,
        })

    @app.exception_handler(DataFileError)
    async def handle_data_file(request: Request, exc: DataFileError):
        return JSONResponse(status_code=500, content={"error": exc.detail})

    @app.exception_handler(FixError)
    async def handle_fix(request: Request, exc: FixError):
        return JSONResponse(status_code=500, content={"error": exc.detail})

    @app.exception_handler(ConfigError)
    async def handle_config(request: Request, exc: ConfigError):
        return JSONResponse(status_code=500, content={"error": exc.detail})

    @app.exception_handler(ConcurrencyError)
    async def handle_concurrency(request: Request, exc: ConcurrencyError):
        return JSONResponse(status_code=412, content={"error": exc.detail})

    @app.exception_handler(GitError)
    async def handle_git(request: Request, exc: GitError):
        return JSONResponse(status_code=500, content={"error": exc.detail})

    @app.exception_handler(AppError)
    async def handle_app(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    @app.exception_handler(Exception)
    async def handle_generic(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"error": str(exc)})
