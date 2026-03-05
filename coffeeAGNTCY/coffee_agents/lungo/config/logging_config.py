# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# logging_config.py
import logging
import sys
from datetime import datetime, timezone

from config.config import LOGGING_LEVEL


class UtcMillisFormatter(logging.Formatter):
    """Formatter with UTC timestamp and milliseconds: YYYY-MM-DD HH:mm:ss.mmm"""

    def formatTime(self, record, datefmt=None):
        utc = datetime.fromtimestamp(record.created, tz=timezone.utc)
        base = utc.strftime("%Y-%m-%d %H:%M:%S")
        ms = int((record.created % 1) * 1000)
        return f"{base}.{ms:03d}"


class FlushingStreamHandler(logging.StreamHandler):
    """StreamHandler that flushes after every emit so log lines appear immediately."""

    def emit(self, record):
        try:
            super().emit(record)
            self.flush()
        except (ValueError, OSError):
            msg = self.format(record)
            try:
                sys.stderr.write(msg + self.terminator)
                sys.stderr.flush()
            except (ValueError, OSError):
                pass


def setup_logging():
    formatter = UtcMillisFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s"
    )
    handler = FlushingStreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(LOGGING_LEVEL)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(LOGGING_LEVEL)

    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


setup_logging()
