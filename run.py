#!/usr/bin/env python3
"""开发服务器入口。"""
import uvicorn

from src.match_maintain.config import get_settings


def main():
    settings = get_settings()
    uvicorn.run(
        "src.match_maintain.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=settings.reload or True,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
