# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Workflow catalog lookup for workflow event emission.

Workflow identity (name + instance_id) is propagated via OpenTelemetry
baggage (see ``common.workflow_context_prop``). This module resolves a
propagated workflow name to catalog metadata.

Agents load the catalog from ``GET /agentic-workflows/``
(Bearer ``WORKFLOW_API_KEY``). A successful GET is cached for the process.
A failed GET is cached as empty for ``_NEGATIVE_CACHE_SECONDS`` so lookups
in that window do not retry or re-log; the miss is cleared when the window
ends. The API process is the only parser of ``starting_workflows.json``.

Catalog lookup is best-effort: a missing or failed catalog does not raise.
Callers log and skip topology emission so agent work continues. The first
GET failure in a window is logged at error (including the retry wait);
an unknown workflow name after a successful load is a warning.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from config.config import WORKFLOW_API_KEY, WORKFLOW_API_URL

logger = logging.getLogger("lungo.common.workflow_catalog")

_CATALOG_PATH = "/agentic-workflows/"
_TIMEOUT_SECONDS = 5.0
_NEGATIVE_CACHE_SECONDS = 15.0

_cached_catalog: dict[str, WorkflowMetadata] | None = None
_negative_until: float | None = None


class WorkflowMetadata(BaseModel):
    """Four catalog identity fields (event_v1 ``$defs.workflow_metadata``)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    pattern: str = Field(min_length=1)
    use_case: str = Field(min_length=1)
    scenario: str = Field(min_length=1)


def _clear_catalog_cache() -> None:
    """Drop the process cache so the next lookup performs a GET."""
    global _cached_catalog, _negative_until
    _cached_catalog = None
    _negative_until = None


def _negative_cache_active() -> bool:
    """True while a recent failed GET should be reused without retrying."""
    global _negative_until
    if _negative_until is None:
        return False
    if time.monotonic() >= _negative_until:
        _negative_until = None
        return False
    return True


def _cache_catalog_failure() -> None:
    """Remember a failed GET until ``_NEGATIVE_CACHE_SECONDS`` elapses."""
    global _negative_until
    _negative_until = time.monotonic() + _NEGATIVE_CACHE_SECONDS
    logger.error(
        "Workflow catalog GET failed; next lookups will wait %.0fs before retry",
        _NEGATIVE_CACHE_SECONDS,
    )


def _fetch_catalog_payload() -> dict[str, Any] | None:
    """GET the workflow summary map. Returns None on transport or HTTP failure.

    The GET is a blocking ``httpx.Client`` call. ``lookup_workflow`` stays
    synchronous because MCP wrap and recruiter discovery call it from sync
    code. Async A2A middleware also uses this path; after a successful load
    the process cache makes later lookups in-memory. Failures are remembered
    for ``_NEGATIVE_CACHE_SECONDS`` so the next lookup does not retry until
    that window ends. Offloading with ``asyncio.to_thread`` is a possible
    later change for async callers only.
    """
    base = WORKFLOW_API_URL.rstrip("/")
    url = f"{base}{_CATALOG_PATH}"
    headers: dict[str, str] = {}
    if WORKFLOW_API_KEY:
        headers["Authorization"] = f"Bearer {WORKFLOW_API_KEY}"
    try:
        with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
            response = client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        logger.error("Workflow catalog GET failed (%s: %s)", type(exc).__name__, exc)
        return None
    if response.is_error:
        logger.error(
            "Workflow catalog GET failed status=%s url=%s",
            response.status_code,
            url,
        )
        return None
    try:
        payload = response.json()
    except ValueError as exc:
        logger.error("Workflow catalog GET returned non-JSON: %s", exc)
        return None
    if not isinstance(payload, dict):
        logger.error(
            "Workflow catalog GET expected object, got %s",
            type(payload).__name__,
        )
        return None
    return payload


def _entry_to_metadata(entry: Any) -> WorkflowMetadata | None:
    if not isinstance(entry, dict):
        return None
    try:
        return WorkflowMetadata(
            name=entry["name"],
            pattern=entry["pattern"],
            use_case=entry["use_case"],
            scenario=entry["scenario"],
        )
    except (KeyError, TypeError, ValidationError):
        return None


def _parse_catalog(payload: dict[str, Any]) -> dict[str, WorkflowMetadata]:
    catalog: dict[str, WorkflowMetadata] = {}
    for idx, (key, entry) in enumerate(payload.items()):
        metadata = _entry_to_metadata(entry)
        if metadata is None:
            logger.warning(
                "Skipping workflow catalog entry %r at index %d: missing identity fields",
                key,
                idx,
            )
            continue
        catalog[metadata.name] = metadata
    return catalog


def _load_catalog() -> dict[str, WorkflowMetadata]:
    """Return the cached catalog, or GET once if no successful cache exists."""
    global _cached_catalog
    if _cached_catalog is not None:
        return _cached_catalog
    if _negative_cache_active():
        return {}
    payload = _fetch_catalog_payload()
    if payload is None:
        _cache_catalog_failure()
        return {}
    catalog = _parse_catalog(payload)
    if not catalog:
        logger.error("Workflow catalog GET succeeded but contained no valid entries")
        _cache_catalog_failure()
        return {}
    logger.info("Loaded %d workflow(s) from catalog GET", len(catalog))
    _cached_catalog = catalog
    return catalog


def lookup_workflow(workflow_name: str | None) -> WorkflowMetadata | None:
    """Return WorkflowMetadata for ``workflow_name`` or None if not in catalog.

    Returns None when ``workflow_name`` is falsy, the catalog GET failed, or
    the name is absent. A failed GET is reused for
    ``_NEGATIVE_CACHE_SECONDS``; after that the next lookup retries.
    This is intentional fail-soft: callers log and skip emission instead of
    crashing the agent.
    """
    if not workflow_name:
        return None
    return _load_catalog().get(workflow_name)
