# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Drift guard: auction workflow-name constants must match the catalog.

The auction graph uses string constants for workflow names rather than importing
from the FastAPI loader at ``api/agentic_workflows/workflows.py`` (which would
couple the graph to server-startup lifecycle). This test catches the moment
``starting_workflows.json`` and the constants disagree.
"""

import json
from pathlib import Path

from agents.supervisors.auction.graph.graph import (
    _WORKFLOW_NAME_SERVE,
    _WORKFLOW_NAME_STREAM,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_STARTING_WORKFLOWS_JSON = (
    _REPO_ROOT / "api" / "agentic_workflows" / "starting_workflows.json"
)


def test_auction_workflow_names_match_starting_workflows_json():
    raw = _STARTING_WORKFLOWS_JSON.read_text()
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AssertionError(
            f"{_STARTING_WORKFLOWS_JSON} is not valid JSON: {e}"
        ) from e

    catalog = {
        wf.get("name") for wf in entries if isinstance(wf, dict) and wf.get("name")
    }
    assert _WORKFLOW_NAME_SERVE in catalog, (
        f"{_WORKFLOW_NAME_SERVE!r} not found in {_STARTING_WORKFLOWS_JSON}; "
        "the auction graph constant has drifted from the workflow catalog."
    )
    assert _WORKFLOW_NAME_STREAM in catalog, (
        f"{_WORKFLOW_NAME_STREAM!r} not found in {_STARTING_WORKFLOWS_JSON}; "
        "the auction graph constant has drifted from the workflow catalog."
    )
