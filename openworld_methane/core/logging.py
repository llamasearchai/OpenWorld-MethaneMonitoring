"""Structured logging configuration for OpenWorld Methane Monitoring."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from pydantic import BaseModel


class LogConfig(BaseModel):
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = "json"
    output: str = "stderr"


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)

        if record.exc_info and record.exc_info != True:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(config: LogConfig | None = None) -> logging.Logger:
    """Set up structured logging for the application.
    
    Args:
        config: Optional logging configuration. Uses defaults if not provided.
        
    Returns:
        The root logger instance.
    """
    if config is None:
        config = LogConfig()

    # Configure root logger
    root_logger = logging.getLogger("openworld_methane")
    root_logger.setLevel(getattr(logging, config.level.upper()))

    # Remove any existing handlers
    root_logger.handlers.clear()

    # Set up handler
    if config.output == "stderr":
        handler = logging.StreamHandler(sys.stderr)
    elif config.output == "stdout":
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(config.output)

    # Set up formatter
    if config.format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.
    
    Args:
        name: The logger name, typically __name__.
        
    Returns:
        A logger instance.
    """
    return logging.getLogger(f"openworld_methane.{name}")


def log_with_context(logger: logging.Logger, level: int, message: str, **context: Any) -> None:
    """Log a message with additional context data.
    
    Args:
        logger: The logger instance.
        level: The log level.
        message: The log message.
        **context: Additional context data to include in the log entry.
    """
    extra = {"extra_data": context}
    logger.log(level, message, extra=extra)


def log_error_with_context(
    logger: logging.Logger,
    message: str,
    exception: Exception | None = None,
    **context: Any
) -> None:
    """Log an error with context and optional exception details.
    
    Args:
        logger: The logger instance.
        message: The error message.
        exception: Optional exception to log.
        **context: Additional context data.
    """
    extra = {"extra_data": context}
    if exception:
        logger.error(message, exc_info=exception, extra=extra)
    else:
        logger.error(message, extra=extra)
