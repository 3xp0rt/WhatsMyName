"""Shared logging utilities for WhatsMyName scripts."""

import logging

from rich.logging import RichHandler
from wmn_constants import LOGGER_NAME


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure Rich logger with tracebacks and time display."""
    logger = logging.getLogger(LOGGER_NAME)

    if not logger.handlers:
        handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=False,
        )
        handler.setLevel(level)

        logger.setLevel(level)
        logger.addHandler(handler)
        logger.propagate = False

    return logger
