# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit-test fixtures shared under ``tests/unit/``."""

from __future__ import annotations

import pytest

import config.config as config_mod
from tests.helpers.workflow_api_auth import (
    TEST_WORKFLOW_API_KEY,
    workflow_api_auth_headers,
)


@pytest.fixture(autouse=True)
def _workflow_api_key_for_unit_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WORKFLOW_API_KEY", TEST_WORKFLOW_API_KEY)
    monkeypatch.setattr(config_mod, "WORKFLOW_API_KEY", TEST_WORKFLOW_API_KEY)


@pytest.fixture
def workflow_api_headers() -> dict[str, str]:
    return workflow_api_auth_headers()
