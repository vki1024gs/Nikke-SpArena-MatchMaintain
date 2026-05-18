"""请求日志中间件。"""
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.monotonic()
        logger.debug(f"→ {request.method} {request.url.path} [{request.client.host if request.client else '?'}]")

        response = await call_next(request)

        duration = time.monotonic() - start
        response.headers["X-Process-Time"] = f"{duration:.3f}s"
        response.headers["X-Request-ID"] = request_id

        logger.debug(f"← {request.method} {request.url.path} {response.status_code} ({duration*1000:.1f}ms)")
        return response
