# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Drift guard: logistics workflow-name constant must match the catalog."""

from agents.supervisors.logistics.graph.graph import _WORKFLOW_NAME
from tests.helpers.workflow_names import assert_workflow_name_in_catalog


def test_logistics_workflow_name_matches_starting_workflows_json():
    assert_workflow_name_in_catalog(_WORKFLOW_NAME, "logistics graph")
