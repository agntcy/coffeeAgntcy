# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Drift guard: recruiter workflow-name constant must match the catalog."""

from tests.helpers.workflow_names import assert_workflow_name_in_catalog


def test_recruiter_workflow_name_matches_starting_workflows_json(recruiter_agent):
    assert_workflow_name_in_catalog(recruiter_agent._WORKFLOW_NAME, "recruiter agent")
