"""
GitHub Crawler - Logging Utility

Provides consistent logging across all modules with configurable verbosity.
"""

import logging
import sys
from typing import Optional

# Default log format
LOG_FORMAT = '[%(asctime)s] [%(levelname)s] %(name)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Log level mapping
LEVEL_MAP = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}

# Global logger registry
_loggers: dict = {}
_root_configured: bool = False


def setup_logging(
    level: str = 'info',
    log_file: Optional[str] = None,
    format_str: str = LOG_FORMAT
) -> None:
    """
    Configure root logging.

    Args:
        level: Log level ('debug', 'info', 'warning', 'error')
        log_file: Optional file path for log output
        format_str: Log message format string
    """
    global _root_configured

    log_level = LEVEL_MAP.get(level.lower(), logging.INFO)
    handlers: list = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(format_str, datefmt=DATE_FORMAT))
    handlers.append(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # File always gets debug
        file_handler.setFormatter(logging.Formatter(format_str, datefmt=DATE_FORMAT))
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True,
    )

    _root_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    if not _root_configured:
        setup_logging('info')

    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)

    return _loggers[name]


class ProgressTracker:
    """Simple progress tracker for batch operations."""

    def __init__(self, total: int, logger_name: str = __name__, label: str = "Progress"):
        self.total = total
        self.current = 0
        self.label = label
        self.log = get_logger(logger_name)

    def update(self, increment: int = 1) -> None:
        """Update progress by increment."""
        self.current += increment
        pct = (self.current / self.total * 100) if self.total > 0 else 0
        self.log.info(f"{self.label}: {self.current}/{self.total} ({pct:.1f}%)")

    def finish(self) -> None:
        """Mark as complete."""
        self.log.info(f"{self.label}: Complete ({self.total}/{self.total})")
