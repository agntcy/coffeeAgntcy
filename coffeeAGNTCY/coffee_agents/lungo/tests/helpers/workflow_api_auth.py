# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared Bearer token for Agentic Workflows API tests."""

from __future__ import annotations

TEST_WORKFLOW_API_KEY = "test-workflow-api-key-for-pytest-only"


def workflow_api_auth_headers(
    key: str | None = None,
) -> dict[str, str]:
    token = key if key is not None else TEST_WORKFLOW_API_KEY
    return {"Authorization": f"Bearer {token}"}
