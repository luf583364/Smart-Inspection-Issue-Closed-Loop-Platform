import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings

LOG_DIR = settings.BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level="DEBUG" if settings.APP_ENV == "dev" else "INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>",
    )
    logger.add(
        LOG_DIR / "app.log",
        level="INFO",
        rotation="10 MB",
        retention="14 days",
        encoding="utf-8",
        enqueue=True,
    )


__all__ = ["logger", "setup_logger"]
