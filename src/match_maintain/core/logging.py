"""日志配置。"""
import sys
import logging
from pathlib import Path

from loguru import logger


def setup_logging(level: str = "INFO", log_format: str = "text", log_file: Path | None = None) -> None:
    """配置 loguru 日志。"""
    logger.remove()

    if log_format == "json":
        fmt = "{time:YYYY-MM-DDTHH:mm:ss.SSSZ} | {level} | {name}:{function}:{line} - {message}"
        logger.add(sys.stderr, level=level.upper(), format=fmt, serialize=True)
    else:
        fmt = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        logger.add(sys.stderr, level=level.upper(), format=fmt, colorize=True)

    if log_file:
        logger.add(
            str(log_file),
            level="DEBUG",
            rotation="10 MB",
            retention="7 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        )

    # 拦截标准 logging
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            frame, depth = sys._getframe(6), 6
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0)
