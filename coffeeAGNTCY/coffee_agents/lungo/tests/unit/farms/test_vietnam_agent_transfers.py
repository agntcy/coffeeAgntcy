# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the delegation wiring of the Vietnam farm agent team.

The coordinator delegates each request to one specialist. The specialists are
leaf agents that must answer, never transfer: with ADK's defaults a specialist
may transfer back to the coordinator (or to a peer), which makes the agents
bounce the request between each other until one of them ends the loop, often
with the general agent's fallback instead of the inventory estimate.
"""

from __future__ import annotations

import pytest

from agents.farms.vietnam.agent import (
    general_agent,
    inventory_agent,
    orders_agent,
    root_agent,
)

SPECIALISTS = [general_agent, inventory_agent, orders_agent]


@pytest.mark.parametrize("specialist", SPECIALISTS, ids=lambda a: a.name)
def test_specialist_cannot_transfer_back_to_the_coordinator(specialist):
    assert specialist.disallow_transfer_to_parent is True


@pytest.mark.parametrize("specialist", SPECIALISTS, ids=lambda a: a.name)
def test_specialist_cannot_transfer_to_a_peer(specialist):
    assert specialist.disallow_transfer_to_peers is True


def test_coordinator_delegates_to_exactly_the_specialists():
    assert {a.name for a in root_agent.sub_agents} == {a.name for a in SPECIALISTS}
