"""Centralized logging configuration for the application.

This module provides a single source of truth for logging configuration,
avoiding duplication and ensuring consistency across the application.
"""
import logging
import structlog
from pathlib import Path
from typing import Optional


def get_log_level(level_str: str) -> int:
    """
    Convert string log level to logging constant.

    Args:
        level_str: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Corresponding logging level constant

    Raises:
        ValueError: If log level string is invalid
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    level_upper = level_str.upper()
    if level_upper not in level_map:
        raise ValueError(
            f"Invalid log level: {level_str}. "
            f"Must be one of: {', '.join(level_map.keys())}"
        )

    return level_map[level_upper]


def configure_structlog(
    log_level: str = "INFO",
    use_json: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    Configure structlog with consistent settings.

    This is the single source of truth for structlog configuration.
    Should be called once at application startup.

    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: If True, use JSON output; if False, use console-friendly output
        log_file: Optional path to log file. If provided, logs to both file and console.

    Example:
        >>> from src.infrastructure.api.config import settings
        >>> configure_structlog(
        ...     log_level=settings.LOG_LEVEL,
        ...     use_json=(settings.LOG_FORMAT == "json"),
        ...     log_file=settings.LOG_FILE
        ... )
    """
    level = get_log_level(log_level)

    # Configure Python's standard logging
    handlers = [logging.StreamHandler()]

    if log_file:
        # Create log directory if needed
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))

    logging.basicConfig(
        format="%(message)s",
        level=level,
        handlers=handlers
    )

    # Choose processor based on output format
    if use_json:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
