"""Structured logging configuration for MyAgent.

Provides JSON-formatted logs with rotation support for production deployments.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def __init__(self, include_extra: bool = True) -> None:
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if self.include_extra:
            # Include any extra fields added to the log record
            for key, value in record.__dict__.items():
                if key not in {
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "message",
                    "asctime",
                    "getMessage",
                }:
                    try:
                        json.dumps({key: value})  # Validate serializable
                        log_data[key] = value
                    except (TypeError, ValueError):
                        log_data[key] = str(value)

        return json.dumps(log_data, ensure_ascii=False, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter."""

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, fmt: str | None = None) -> None:
        super().__init__(fmt or "%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET if color else ""
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    json_format: bool = False,
    enable_console: bool = True,
) -> None:
    """Configure logging for MyAgent.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None for no file logging)
        max_bytes: Max size of log file before rotation
        backup_count: Number of backup files to keep
        json_format: Use JSON formatting for file logs
        enable_console: Enable console output
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = ColoredFormatter()
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        if json_format:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
