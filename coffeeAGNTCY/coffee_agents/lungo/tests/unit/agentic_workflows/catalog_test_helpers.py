# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared helpers for unit tests that load ``starting_workflows.json`` directly."""

from __future__ import annotations

from pathlib import Path

from api.agentic_workflows.transport_ui_enrichment import init_transport_cache
from api.agentic_workflows.workflows import _load_and_validate_starting_workflows_from_file
from schema.types import Workflow

_LUNGO_ROOT = Path(__file__).resolve().parents[3]
STARTING_WORKFLOWS_JSON = (
    _LUNGO_ROOT / "api" / "agentic_workflows" / "starting_workflows.json"
)


def load_validated_starting_workflows_catalog(
    target: Path | None = None,
) -> dict[str, Workflow]:
    """Load and validate the starting-workflows catalog without ``set_starting_workflows()``.

    This mirrors the catalog load performed at server startup but does not mutate
    the global ``_STARTING_WORKFLOWS`` cache.
    """
    return _load_and_validate_starting_workflows_from_file(target or STARTING_WORKFLOWS_JSON)


def init_transport_cache_for_tests() -> None:
    """Initialize transport enrichment facts for tests.

    ``init_transport_cache()`` is only called from ``set_starting_workflows()`` at
    server startup. Any test that loads the catalog via
    ``load_validated_starting_workflows_catalog()`` and then asserts transport wire
    enrichment (``message_transport``, ``Transport: …`` labels) must call this helper
    or use ``load_catalog_with_transport_cache()`` first.
    """
    init_transport_cache()


def load_catalog_with_transport_cache(
    target: Path | None = None,
) -> dict[str, Workflow]:
    """Load the validated catalog and initialize transport enrichment for tests."""
    catalog = load_validated_starting_workflows_catalog(target)
    init_transport_cache_for_tests()
    return catalog
