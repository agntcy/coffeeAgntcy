# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared CORS allowlist parsing for Lungo HTTP services (browser UI origins)."""

from __future__ import annotations

import os

# Browser origins for local Lungo UI (vite port 3000). Distinct from API URL.
DEFAULT_CORS_ALLOWED_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def get_cors_allowed_origins() -> list[str]:
    """Parse ``CORS_ALLOWED_ORIGINS`` (comma-separated); fall back to local UI defaults."""
    raw = os.environ.get("CORS_ALLOWED_ORIGINS", "").strip()
    parsed = [part.strip() for part in raw.split(",") if part.strip()]

    return parsed if parsed else DEFAULT_CORS_ALLOWED_ORIGINS
