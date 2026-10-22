# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Snapshot tests for the lungo agent cards (a2a-sdk 1.x shape).

The first ``supported_interfaces`` entry is the transport an agent prefers,
so the binding order is part of each card's contract. URLs come from the
environment, so only their scheme is pinned here.
"""

from __future__ import annotations

import importlib
from urllib.parse import urlparse

import pytest
from google.protobuf.json_format import MessageToDict

_FARM = [("slimpatterns", "slim"), ("natspatterns", "nats"), ("jsonrpc", "http")]
_LOGISTICS = [("slimpatterns", "slim")]

CARDS = [
    ("agents.farms.brazil.card", "AGENT_CARD", "Brazil Coffee Farm", _FARM),
    ("agents.farms.colombia.card", "AGENT_CARD", "Colombia Coffee Farm", _FARM),
    ("agents.farms.vietnam.card", "AGENT_CARD", "Vietnam Coffee Farm", _FARM),
    ("agents.logistics.accountant.card", "AGENT_CARD", "Accountant agent", _LOGISTICS),
    ("agents.logistics.farm.card", "AGENT_CARD", "Tatooine Farm agent", _LOGISTICS),
    ("agents.logistics.helpdesk.card", "AGENT_CARD", "Logistics Helpdesk", _LOGISTICS),
    ("agents.logistics.shipper.card", "AGENT_CARD", "Shipping agent", _LOGISTICS),
    (
        "agents.supervisors.auction.card",
        "AUCTION_SUPERVISOR_CARD",
        "Auction Supervisor agent",
        [],
    ),
    (
        "agents.supervisors.logistics.card",
        "LOGISTICS_SUPERVISOR_CARD",
        "Logistics Supervisor agent",
        [],
    ),
    (
        "agents.supervisors.recruiter.card",
        "RECRUITER_SUPERVISOR_CARD",
        "Recruiter Supervisor",
        [],
    ),
    (
        "agents.supervisors.recruiter.recruiter_service_card",
        "RECRUITER_AGENT_CARD",
        "RecruiterAgent",
        [("JSONRPC", "http")],
    ),
]

_V03_ONLY_KEYS = {
    "url",
    "preferredTransport",
    "additionalInterfaces",
    "protocolVersion",
    "supportsAuthenticatedExtendedCard",
    "id",
}


def _card(module_name: str, attr: str):
    return getattr(importlib.import_module(module_name), attr)


@pytest.mark.parametrize(
    "module_name,attr,name,expected", CARDS, ids=[c[0] for c in CARDS]
)
def test_card_interfaces_in_preference_order(module_name, attr, name, expected):
    card = _card(module_name, attr)

    assert card.name == name
    assert [
        (i.protocol_binding, urlparse(i.url).scheme)
        for i in card.supported_interfaces
    ] == expected


@pytest.mark.parametrize(
    "module_name,attr,name,expected", CARDS, ids=[c[0] for c in CARDS]
)
def test_card_has_no_v03_only_fields(module_name, attr, name, expected):
    card_json = MessageToDict(_card(module_name, attr))

    assert _V03_ONLY_KEYS.isdisjoint(card_json)
    assert card_json["capabilities"]["streaming"] is True


def test_recruiter_service_card_targets_the_v03_service():
    """The recruiter service still speaks A2A v0.3, so the client picks the compat transport."""
    card = _card(
        "agents.supervisors.recruiter.recruiter_service_card", "RECRUITER_AGENT_CARD"
    )
    [interface] = card.supported_interfaces
    assert interface.protocol_version == "0.3"
