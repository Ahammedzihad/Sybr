"""Structured and safe application logging."""

import logging
import re
import sys
from typing import Any
from app.core.config import settings

# Sensitive key patterns to mask in logs
MASK_PATTERNS = [
    (re.compile(r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE), r'\1[MASKED]'),
    (re.compile(r'(authorization["\']?\s*[:=]\s*["\']?Bearer\s+)([^"\'\s]+)', re.IGNORECASE), r'\1[MASKED]'),
    (re.compile(r'(password["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE), r'\1[MASKED]'),
]


class SensitiveDataFilter(logging.Filter):
    """Filter that sanitizes credentials and API keys from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in MASK_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True


def setup_logger(name: str = "security_app") -> logging.Logger:
    """Configures and returns a safe structured logger."""
    logger = logging.getLogger(name)
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = setup_logger()
