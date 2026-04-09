"""Logging utilities.

Creates a consistent logger for the app (console + rotating file).
"""

from __future__ import annotations

import logging
import os
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

_logger_lock = threading.Lock()


def get_logger(name: str = "myai", log_dir: str | os.PathLike = "logs") -> logging.Logger:
    logger = logging.getLogger(name)

    with _logger_lock:
        if getattr(logger, "_configured", False):
            return logger

        level_name = os.getenv("LOG_LEVEL", "INFO").upper().strip()
        level = getattr(logging, level_name, logging.INFO)
        logger.setLevel(level)
        logger.propagate = False

        fmt = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        sh = logging.StreamHandler()
        sh.setLevel(level)
        sh.setFormatter(fmt)
        logger.addHandler(sh)

        log_file = os.getenv("LOG_FILE") or str(Path(log_dir) / "myaidoc.log")
        try:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            fh = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
            fh.setLevel(level)
            fh.setFormatter(fmt)
            logger.addHandler(fh)
        except Exception:
            logger.warning("File logging disabled; failed to initialize log file: %s", log_file)

        logger._configured = True  # type: ignore[attr-defined]
        logger.debug("Logger configured (level=%s, file=%s)", level_name, log_file)
    return logger
