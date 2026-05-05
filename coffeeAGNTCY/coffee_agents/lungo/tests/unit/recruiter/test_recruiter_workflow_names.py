# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Drift guard: recruiter workflow-name constant must match the catalog."""

import json
from pathlib import Path

from agents.supervisors.recruiter.agent import _WORKFLOW_NAME

_REPO_ROOT = Path(__file__).resolve().parents[3]
_STARTING_WORKFLOWS_JSON = (
    _REPO_ROOT / "api" / "agentic_workflows" / "starting_workflows.json"
)


def test_recruiter_workflow_name_matches_starting_workflows_json():
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
    assert _WORKFLOW_NAME in catalog, (
        f"{_WORKFLOW_NAME!r} not found in {_STARTING_WORKFLOWS_JSON}; "
        "the recruiter agent constant has drifted from the workflow catalog."
    )
