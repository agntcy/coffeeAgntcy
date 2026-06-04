# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Drift guard: the workflow names hard-coded in auction graph.py must
match entries in api/agentic_workflows/starting_workflows.json.

The hard-coding is a TEMP shim until the UI/API supplies workflow_name on
every request (see common/workflow_context_prop.py). When that lands, both
the constants and this test go away together.
"""

from __future__ import annotations

from agents.supervisors.auction.graph.graph import (
    _WORKFLOW_NAME_SERVE,
    _WORKFLOW_NAME_STREAM,
)
from common.workflow_utils.workflow_catalog import lookup_workflow


def test_serve_workflow_name_in_catalog():
    identity = lookup_workflow(_WORKFLOW_NAME_SERVE)
    assert identity is not None, f"{_WORKFLOW_NAME_SERVE!r} missing from catalog"
    assert identity.workflow_name == _WORKFLOW_NAME_SERVE


def test_stream_workflow_name_in_catalog():
    identity = lookup_workflow(_WORKFLOW_NAME_STREAM)
    assert identity is not None, f"{_WORKFLOW_NAME_STREAM!r} missing from catalog"
    assert identity.workflow_name == _WORKFLOW_NAME_STREAM
