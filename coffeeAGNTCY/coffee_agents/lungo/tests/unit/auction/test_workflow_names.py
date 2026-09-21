# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Drift guard: the workflow names hard-coded in auction graph.py must
match entries in api/agentic_workflows/starting_workflows.json.

The hard-coding is a TEMP shim until the UI/API supplies workflow_name on
every request (see common.workflow_context_prop.py). When that lands, both
the constants and this test go away together.
"""

from __future__ import annotations

from agents.supervisors.auction.graph.graph import (
    _WORKFLOW_NAME_SERVE,
    _WORKFLOW_NAME_STREAM,
)
from tests.helpers.workflow_names import assert_workflow_name_in_catalog


def test_serve_workflow_name_in_catalog():
    assert_workflow_name_in_catalog(_WORKFLOW_NAME_SERVE, "auction graph")


def test_stream_workflow_name_in_catalog():
    assert_workflow_name_in_catalog(_WORKFLOW_NAME_STREAM, "auction graph")
