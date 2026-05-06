# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Drift guard: auction workflow-name constants must match the catalog."""

from agents.supervisors.auction.graph.graph import (
    _WORKFLOW_NAME_SERVE,
    _WORKFLOW_NAME_STREAM,
)
from tests.helpers.workflow_names import assert_workflow_name_in_catalog


def test_auction_workflow_names_match_starting_workflows_json():
    assert_workflow_name_in_catalog(_WORKFLOW_NAME_SERVE, "auction graph")
    assert_workflow_name_in_catalog(_WORKFLOW_NAME_STREAM, "auction graph")
