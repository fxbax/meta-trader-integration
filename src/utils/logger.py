# src/utils/logger.py
import logging
from logging.handlers import RotatingFileHandler
import os
import re
from pathlib import Path
from config.settings import settings


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive information (passwords, tokens) in logs."""

    PASSWORD_PATTERN = re.compile(r'(["\']?password["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE)
    TOKEN_PATTERN = re.compile(r'(["\']?(?:token|AUTH_TOKEN)["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE)

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.PASSWORD_PATTERN.sub(r'\1***MASKED***\3', record.msg)
            record.msg = self.TOKEN_PATTERN.sub(r'\1***MASKED***\3', record.msg)
        return True


def setup_logger(name: str = "fxbax_mt") -> logging.Logger:
    """Setup and configure application logger with console and rotating file handlers."""
    logger = logging.getLogger(name)
    level = getattr(logging, settings.log_level, logging.INFO)
    logger.setLevel(level)

    # Prevent duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    sensitive_filter = SensitiveDataFilter()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(sensitive_filter)
    logger.addHandler(console_handler)

    # File handler (if directory can be created / exists)
    try:
        log_dir = Path(settings.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        file_path = log_dir / "service.log"

        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(sensitive_filter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not setup file logging: {e}")

    return logger


logger = setup_logger()
