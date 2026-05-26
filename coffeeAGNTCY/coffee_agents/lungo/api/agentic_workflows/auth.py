# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Bearer authentication for the Agentic Workflows API."""

from __future__ import annotations

import secrets

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.config import WORKFLOW_API_KEY

_bearer = HTTPBearer(auto_error=False)


def require_workflow_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> None:
    """Reject requests without a valid ``Authorization: Bearer`` token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not WORKFLOW_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not secrets.compare_digest(credentials.credentials, WORKFLOW_API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized")


def assert_workflow_api_key_configured() -> None:
    """Fail fast when the API key is missing (startup)."""
    if not WORKFLOW_API_KEY or not WORKFLOW_API_KEY.strip():
        msg = (
            "WORKFLOW_API_KEY is unset or empty; set it to protect the "
            "Agentic Workflows API"
        )
        raise RuntimeError(msg)
