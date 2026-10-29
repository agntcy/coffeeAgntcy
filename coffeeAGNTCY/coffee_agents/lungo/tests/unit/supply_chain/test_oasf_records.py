# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""OASF records match their agent cards (name, id and SLIM interface)."""

import json
from pathlib import Path
from urllib.parse import urlparse

import pytest

from agents.supply_chain.logistics.card import AGENT_CARD as LOGISTICS_CARD
from agents.supply_chain.supplier.card import AGENT_CARDS, agent_id

OASF_DIR = (
    Path(__file__).resolve().parents[3]
    / "agents"
    / "supervisors"
    / "supply_chain"
    / "oasf"
    / "agents"
)

CARDS = {agent_id(sid): card for sid, card in AGENT_CARDS.items()}
CARDS["supply-chain-logistics-agent"] = LOGISTICS_CARD


def _load(slug: str) -> dict:
    return json.loads((OASF_DIR / f"{slug}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("slug", sorted(CARDS))
def test_oasf_name_equals_card_name(slug):
    record = _load(slug)
    card_data = record["modules"][0]["data"]["card_data"]
    assert record["name"] == card_data["name"] == CARDS[slug].name


@pytest.mark.parametrize("slug", sorted(CARDS))
def test_oasf_slim_url_ends_with_the_agent_id(slug):
    card_data = _load(slug)["modules"][0]["data"]["card_data"]
    assert urlparse(card_data["url"]).path == f"/lungo/agents/{slug}"
    assert (
        urlparse(CARDS[slug].supported_interfaces[0].url).path
        == f"/lungo/agents/{slug}"
    )


def test_buyer_oasf_record_matches_the_buyer_card():
    from agents.supervisors.supply_chain.card import BUYER_CARD

    record = _load("supply-chain-buyer-agent")
    card_data = record["modules"][0]["data"]["card_data"]
    assert record["name"] == card_data["name"] == BUYER_CARD.name
    assert [s["id"] for s in card_data["skills"]] == [s.id for s in BUYER_CARD.skills]


def test_card_names_are_unique():
    from agents.supervisors.supply_chain.card import BUYER_CARD

    names = [c.name for c in CARDS.values()] + [BUYER_CARD.name]
    assert len(names) == len(set(names)) == 5


def test_supplier_id_env_selects_the_card(monkeypatch):
    from agents.supply_chain.supplier.card import supplier_id_from_env

    monkeypatch.setenv("SUPPLIER_ID", "c")
    assert supplier_id_from_env() == "supplier_c"
    monkeypatch.setenv("SUPPLIER_ID", "d")
    with pytest.raises(ValueError):
        supplier_id_from_env()
