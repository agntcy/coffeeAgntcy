# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""configure_logger must not drop records from modules that use loguru directly."""

import pytest
from loguru import logger as raw_logger

from agent_recruiter.common.logging import LOG_FORMAT, configure_logger, get_logger


@pytest.fixture
def captured():
    configure_logger()
    lines: list[str] = []
    # The sink the real server adds uses LOG_FORMAT; add one that records lines.
    handler_id = raw_logger.add(lines.append, level="INFO", format=LOG_FORMAT)
    yield lines
    raw_logger.remove(handler_id)
    raw_logger.remove(None)
    raw_logger.configure(extra={})


def test_plain_loguru_logger_is_written_with_the_default_name(captured):
    raw_logger.warning("plain {}", "record")

    assert any("| root - plain record" in line for line in captured)


def test_get_logger_name_overrides_the_default(captured):
    get_logger("evaluator").warning("named {}", "record")

    assert any("| evaluator - named record" in line for line in captured)
