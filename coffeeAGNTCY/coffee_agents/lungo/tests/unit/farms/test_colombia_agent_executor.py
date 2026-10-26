# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for Colombia farm executor workflow-identity extraction."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from a2a.types import Message, Part, Role

from agents.farms.colombia.agent_executor import FarmAgentExecutor


def _context(metadata):
    """Request-context stand-in carrying a real a2a-sdk 1.x Message.

    ``Message.metadata`` is a protobuf ``Struct``, not a dict, so this is the
    shape the executor receives at runtime.
    """
    message = Message(
        message_id="m1",
        role=Role.ROLE_USER,
        parts=[Part(text="hi")],
        metadata=metadata,
    )
    return SimpleNamespace(message=message)


@pytest.mark.parametrize(
    "case,context,expected",
    [
        (
            "both_present",
            _context(
                {
                    "workflow_name": "Auction",
                    "workflow_instance_id": "instance://abc",
                }
            ),
            ("Auction", "instance://abc"),
        ),
        ("name_only", _context({"workflow_name": "w"}), ("w", None)),
        (
            "instance_only",
            _context({"workflow_instance_id": "instance://abc"}),
            (None, "instance://abc"),
        ),
        ("empty_metadata", _context({}), (None, None)),
        ("metadata_unset", _context(None), (None, None)),
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
