"""
logger.py — Centralized logging configuration for ChillBot.

Provides a colored console logger with timestamps.
"""

import logging
import sys
from typing import Optional


# ANSI color codes for terminal output
_COLORS = {
    "DEBUG":    "\033[36m",   # Cyan
    "INFO":     "\033[32m",   # Green
    "WARNING":  "\033[33m",   # Yellow
    "ERROR":    "\033[31m",   # Red
    "CRITICAL": "\033[35m",   # Magenta
    "RESET":    "\033[0m",
}


class _ColorFormatter(logging.Formatter):
    """Custom formatter that injects ANSI color codes based on log level."""

    FMT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    DATE_FMT = "%H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        color = _COLORS.get(record.levelname, _COLORS["RESET"])
        reset = _COLORS["RESET"]
        formatter = logging.Formatter(
            f"{color}{self.FMT}{reset}", datefmt=self.DATE_FMT
        )
        return formatter.format(record)


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Return a named logger that writes to stderr only.

    MCP servers communicate with the client over stdio (stdout/stdin).
    Any output written to stdout by a server corrupts the MCP protocol
    stream.  All logging MUST go to stderr so it never interferes.

    Args:
        name:  Logger name (typically __name__ of the calling module).
        level: Optional logging level override (default: INFO).

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when the same logger is requested twice
    if logger.handlers:
        return logger

    logger.setLevel(level or logging.INFO)

    # CRITICAL: use stderr, never stdout — stdout is reserved for MCP protocol
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_ColorFormatter())
    logger.addHandler(handler)

    # Prevent log records from bubbling up to the root logger
    logger.propagate = False

    return logger
