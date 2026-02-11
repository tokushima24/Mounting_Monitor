# src/logger_config.py
"""
Logger Configuration
====================

Configures application-wide logging with file rotation and console output.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(
    name: str = "SwineMonitor",
    log_path: str = "logs/system.log",
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3
) -> logging.Logger:
    """
    Set up and configure a logger with file and console handlers.
    
    Creates a logger that writes to both a rotating log file and the console.
    If the logger already has handlers configured, returns the existing logger
    without modification to avoid duplicate handlers.
    
    Args:
        name: The name of the logger. Default is "SwineMonitor".
        log_path: Path to the log file. Parent directories will be created
                  if they don't exist. Default is "logs/system.log".
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
               Default is logging.INFO.
        max_bytes: Maximum size of each log file before rotation.
                   Default is 5MB.
        backup_count: Number of backup files to keep. Default is 3.
    
    Returns:
        logging.Logger: Configured logger instance.
        
    Examples:
        >>> logger = setup_logger("MyApp", "logs/app.log")
        >>> logger.info("Application started")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(module)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler with rotation
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
