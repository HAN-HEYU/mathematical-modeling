"""Consistent console and file logging for model runs."""

from __future__ import annotations

import logging
from pathlib import Path

from .config import LOGS_DIR
from .data_io import ensure_dir


def setup_logging(
    name: str,
    *,
    log_file: str | Path | None = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Return a logger with one console handler and an optional UTF-8 file."""
    if not name.strip():
        raise ValueError("logger name must not be empty")
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    logger.handlers.clear()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_file is not None:
        target = Path(log_file)
        ensure_dir(target.parent)
        file_handler = logging.FileHandler(target, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


def question_logger(question: str) -> logging.Logger:
    """Create the conventional logger for a question entry point."""
    normalized = question.lower().strip()
    return setup_logging(normalized, log_file=LOGS_DIR / f"{normalized}.log")


__all__ = ["question_logger", "setup_logging"]
