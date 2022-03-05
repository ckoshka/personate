import sys
from loguru import logger

logger.add(
    sys.stdout,
    colorize=True,
    backtrace=True,
    diagnose=True,
    enqueue=True,
    format="<blue>{file}</blue> <green>{function}</green> <red>{level}</red> <cyan>{message}</cyan>",
)
