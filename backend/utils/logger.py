import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
LOGGING_DIR = BASE_DIR / "logs"
LOGGING_DIR.mkdir(exist_ok=True)

path = LOGGING_DIR / "app.log"
file_handler = RotatingFileHandler(
    path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
)


formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)


logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)


console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)