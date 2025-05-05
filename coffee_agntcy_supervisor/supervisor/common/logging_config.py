# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import logging.config
import os
import traceback
from pathlib import Path
from typing import Dict

import coloredlogs

if os.getenv("HTTP_CLIENT_DEBUG", "0") == "1":
  import http.client as http_client

  http_client.HTTPConnection.debuglevel = 1


class JSONFormatter(logging.Formatter):
  """
  Custom logging formatter that outputs logs in structured JSON format.

  - Includes timestamp, log level, message, module, function, and line number.
  - Captures exceptions with stack trace when applicable.
  """

  def format(self, record: logging.LogRecord) -> str:
    log_data = {
      "timestamp": self.formatTime(record), # Corrected: Uses default ISO 8601 format
      "level": record.levelname,
      "message": record.getMessage(),
      "module": record.module,
      "function": record.funcName,
      "line": record.lineno,
      "logger": record.name,
      "pid": record.process,
    }

    # Capture exception details if they exist
    if record.exc_info:
      log_data["error"] = {
        "type": str(record.exc_info[0]),
        "message": str(record.exc_info[1]),
        "stack_trace": traceback.format_exc(),
      }

    return json.dumps(log_data)


def get_log_dir() -> Path:
  """
  Returns the log directory path and ensures it exists.

  Returns:
    Path: The path to the logs directory (app/logs/)
  """
  log_dir = Path(__file__).parent.parent / "logs"
  log_dir.mkdir(parents=True, exist_ok=True)
  return log_dir


def get_log_file() -> Path:
  """
  Returns the log file path and ensures it is removed on every startup.

  Returns:
    Path: The path to the log file (app/logs/remote_graphs.log)
  """

  log_file = get_log_dir() / "remote_graphs.log"

  # Remove old log file on startup to ensure fresh logs
  if log_file.exists():
    log_file.unlink()
  return log_file


def get_log_level() -> str:
  """
  Retrieves the log level from environment variables.

  Defaults to "INFO" if LOG_LEVEL is not set.

  Returns:
    str: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  """
  return os.getenv("LOG_LEVEL", "INFO").upper()


def get_logging_config(log_file: Path, log_level: str) -> Dict:
  """
  Generates the logging configuration dictionary with JSON or colored formatting.

  Args:
    log_file (Path): Path to the log file.
    log_level (str): Logging level (DEBUG, INFO, etc.).

  Returns:
    dict: Logging configuration dictionary.
  """
  formatter = os.getenv("LOG_FORMATTER", "colored").lower()
  handlers = {
    "console": {
      "level": log_level,
      "class": "logging.StreamHandler",
      "formatter": formatter if formatter in ["json", "colored"] else "colored",
    }
  }

  if log_file and os.getenv("LOG_TO_FILE", "0") == "1":
    handlers["file"] = {
      "level": log_level,
      "class": "logging.FileHandler",
      "filename": str(log_file),
      "formatter": "json",
    }

  return {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
      "json": {
        "()": JSONFormatter,  # Use custom JSON formatter
      },
      "colored": {
        "format": "%(asctime)s [%(name)s] [%(levelname)s] [%(funcName)s] %(message)s",
      },
    },
    "handlers": handlers,
    "loggers": {
      "uvicorn": {
        "handlers": list(handlers.keys()),
        "level": log_level,
        "propagate": False,
      },
      "fastapi": {
        "handlers": list(handlers.keys()),
        "level": log_level,
        "propagate": False,
      },
      "app": {
        "handlers": list(handlers.keys()),
        "level": log_level,
        "propagate": False,
      },
      "remote_graphs": {  # Keep for compatibility
        "handlers": list(handlers.keys()),
        "level": log_level,
        "propagate": False,
      },
      "requests.packages.urllib3": {
        "handlers": ["console"],
        "level": log_level,
        "propagate": True,
      },
    },
    "root": {"handlers": list(handlers.keys()), "level": log_level},
  }


def configure_logging() -> None:
  """
  Configures logging for the application.
  This function performs the following tasks:
  - Retrieves the log file path and log level from configuration.
  - Sets up logging using a dictionary-based configuration.
  - Installs coloredlogs for enhanced console output with a specific format.
  - Initializes a logger for the application and logs a message to confirm logging setup.
  Returns:
    None
  """

  log_file = get_log_file() if os.getenv("LOG_TO_FILE", "0") == "1" else None
  log_level = get_log_level()
  logging_config = get_logging_config(log_file, log_level)

  logging.config.dictConfig(logging_config)

  # Install coloredlogs for console output
  coloredlogs.install(level=log_level, fmt="%(asctime)s [%(name)s] [%(levelname)s] [%(funcName)s] %(message)s")

  logger = logging.getLogger("agntcy_agents_common")
  logger.info("Logging has been configured successfully.")

configure_logging()
