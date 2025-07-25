import sys

from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time}</green> | <level>{level}</level> | <level>{message}</level>",
)
