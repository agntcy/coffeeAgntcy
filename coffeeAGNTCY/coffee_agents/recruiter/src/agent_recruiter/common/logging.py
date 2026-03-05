# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Logging configuration using loguru with structured logging support.
Unified format with lungo: UTC timestamp, level, name - message; flush after each write.
"""

import sys
from pathlib import Path
from loguru import logger

# Canonical format matching lungo: YYYY-MM-DD HH:mm:ss.mmm | LEVEL     | name - message
LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS!UTC} | {level: <8} | {extra[name]} - {message}"
)


class _FlushingSink:
    """Wraps a stream and flushes after every write so log lines appear immediately."""

    def __init__(self, stream):
        self._stream = stream

    def write(self, message):
        self._stream.write(message)
        self._stream.flush()

    def flush(self):
        self._stream.flush()


def configure_logger(
    debug: bool = False,
    file_path: Path | str | None = None,
) -> None:
    logger.remove(None)

    level = "DEBUG" if debug else "INFO"

    if file_path:
        logger.add(
            sink=file_path,
            level=level,
            format=LOG_FORMAT,
            backtrace=debug,
            rotation="10 MB",
            colorize=False,
        )
        level = "ERROR"

    logger.add(
        sink=_FlushingSink(sys.stdout),
        level=level,
        format=LOG_FORMAT,
        backtrace=debug,
        colorize=True,
    )


def get_logger(name: str | None = None):
    """
    Get a logger instance.

    Args:
        name: Logger name (defaults to caller's module)

    Returns:
        Configured logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger.bind(name="root")
