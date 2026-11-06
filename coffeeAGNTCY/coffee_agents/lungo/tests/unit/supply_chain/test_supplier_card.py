# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""The supplier card is chosen by SUPPLIER_ID only where it is used."""

import pytest

from agents.supply_chain.supplier import card


def test_supplier_card_is_resolved_on_use(monkeypatch):
    monkeypatch.setenv("SUPPLIER_ID", "x")
    assert set(card.AGENT_CARDS) == {"supplier_a", "supplier_b", "supplier_c"}
    with pytest.raises(ValueError, match="SUPPLIER_ID"):
        _ = card.AGENT_CARD
    monkeypatch.setenv("SUPPLIER_ID", "b")
    assert card.AGENT_CARD is card.AGENT_CARDS["supplier_b"]
