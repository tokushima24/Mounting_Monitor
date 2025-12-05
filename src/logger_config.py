import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(name="SwineMonitor", config_log_path="logs/system.log"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # existing handlersを削除
    if logger.handlers:
        return logger

    # formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(module)s - %(message)s"
    )

    # output file
    log_path = Path(config_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1024 * 1024 * 5,
        backupCount=3,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # output console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
