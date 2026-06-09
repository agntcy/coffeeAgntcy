# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for Colombia farm executor workflow-identity extraction."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from agents.farms.colombia.agent_executor import FarmAgentExecutor


def _context(metadata):
    return SimpleNamespace(message=SimpleNamespace(metadata=metadata))


@pytest.mark.parametrize(
    "case,context,expected",
    [
        (
            "both_present",
            _context({
                "workflow_name": "Auction",
                "workflow_instance_id": "instance://abc",
            }),
            ("Auction", "instance://abc"),
        ),
        ("name_only", _context({"workflow_name": "Auction"}), ("Auction", None)),
        (
            "instance_only",
            _context({"workflow_instance_id": "instance://abc"}),
            (None, "instance://abc"),
        ),
        ("empty_metadata", _context({}), (None, None)),
        ("metadata_none", _context(None), (None, None)),
        ("metadata_not_dict", _context("oops"), (None, None)),
        (
            "non_string_values",
            _context({"workflow_name": 123, "workflow_instance_id": 456}),
            (None, None),
        ),
        ("message_none", SimpleNamespace(message=None), (None, None)),
    ],
)
def test_read_workflow_identity(case, context, expected):
    """Workflow identity is read from A2A message metadata, ignoring bad shapes."""
    assert FarmAgentExecutor._read_workflow_identity(context) == expected
