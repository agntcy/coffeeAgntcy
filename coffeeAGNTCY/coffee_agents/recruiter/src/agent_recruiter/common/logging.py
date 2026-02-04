# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Logging configuration using loguru with structured logging support.
"""

import sys
from pathlib import Path
from loguru import logger


def configure_logger(
    debug: bool = False,
    file_path: Path | str | None = None,
) -> None:
    logger.remove(None)

    level = "DEBUG" if debug else "INFO"

    if file_path:
        # log to file
        logger.add(
            sink=file_path,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message} - {extra}",
            backtrace=debug,
            rotation="10 MB",
            colorize=False,
        )

        # Because we also want to log errors to stdout,
        # changing the level before configuring the stdout logger.
        level = "ERROR"

    logger.add(
        sink=sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level> - {extra}",
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
    return logger
