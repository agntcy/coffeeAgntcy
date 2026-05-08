# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared helper for supervisor workflow-name drift-guard tests."""

from __future__ import annotations

import json
from pathlib import Path

# tests/helpers/workflow_names.py -> parents[2] is repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_STARTING_WORKFLOWS_JSON = (
    _REPO_ROOT / "api" / "agentic_workflows" / "starting_workflows.json"
)


def load_starting_workflow_names() -> set[str]:
    """Return the set of workflow names declared in starting_workflows.json."""
    raw = _STARTING_WORKFLOWS_JSON.read_text()
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AssertionError(
            f"{_STARTING_WORKFLOWS_JSON} is not valid JSON: {e}"
        ) from e

    names: set[str] = set()
    for wf in entries:
        if isinstance(wf, dict):
            name = wf.get("name")
            if isinstance(name, str) and name:
                names.add(name)
    return names


def assert_workflow_name_in_catalog(name: str, supervisor_label: str) -> None:
    """Assert name is present in the starting-workflows catalog.

    supervisor_label appears in the failure message to identify which
    supervisor drifted, e.g. "auction graph", "logistics graph".
    """
    catalog = load_starting_workflow_names()
    assert name in catalog, (
        f"{name!r} not found in {_STARTING_WORKFLOWS_JSON}; "
        f"the {supervisor_label} constant has drifted from the workflow catalog."
    )
