from loguru import logger
import sys
from pathlib import Path

# remove default logger
logger.remove()

# console logs
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level}</level> | "
           "<cyan>{message}</cyan>",
)

# file logs
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger.add(
    "logs/app.log",
    rotation="1 MB",
    level="DEBUG",
)

__all__ = ["logger"]
