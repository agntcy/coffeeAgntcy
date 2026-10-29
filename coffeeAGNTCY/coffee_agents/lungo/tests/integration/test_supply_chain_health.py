# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Health checks for the Supply Chain Commitment agents (SLIM, no LLM calls)."""

import logging

import httpx
import pytest

logger = logging.getLogger(__name__)

TRANSPORT_MATRIX = [
    pytest.param(
        {
            "DEFAULT_MESSAGE_TRANSPORT": "SLIM",
            "TRANSPORT_SERVER_ENDPOINT": "http://127.0.0.1:46357",
        },
        id="SLIM",
    )
]

SUPPLY_CHAIN_MEMBERS = [
    "supply-chain-supplier-a",
    "supply-chain-supplier-b",
    "supply-chain-supplier-c",
    "supply-chain-logistics",
]

# Where each member serves its HTTP health route (the conftest AGENTS ports).
MEMBER_PORTS = {
    "supply-chain-supplier-a": 9096,
    "supply-chain-supplier-b": 9097,
    "supply-chain-supplier-c": 9098,
    "supply-chain-logistics": 9099,
}


@pytest.mark.parametrize("transport_config", TRANSPORT_MATRIX, indirect=True)
class TestSupplyChainMemberHealth:
    @pytest.mark.agents(SUPPLY_CHAIN_MEMBERS)
    @pytest.mark.usefixtures("agents_up")
    @pytest.mark.parametrize("member", SUPPLY_CHAIN_MEMBERS)
    def test_member_is_alive(self, member, transport_config):
        logger.info(f"\n---Test: {member} health with transport {transport_config}---")
        resp = httpx.get(
            f"http://127.0.0.1:{MEMBER_PORTS[member]}/v1/health", timeout=45
        )
        assert resp.status_code == 200
        assert resp.json().get("status") == "alive", f"{member} health check failed"


@pytest.mark.parametrize("transport_config", TRANSPORT_MATRIX, indirect=True)
class TestSupplyChainBuyerHealth:
    @pytest.mark.agents(SUPPLY_CHAIN_MEMBERS)
    @pytest.mark.usefixtures("agents_up")
    def test_buyer_is_alive(self, supply_chain_buyer_client, transport_config):
        resp = supply_chain_buyer_client.get("/v1/health")
        assert resp.status_code == 200
        assert resp.json().get("status") == "alive"

    def test_buyer_answers_the_cheap_routes_without_agents(
        self, supply_chain_buyer_client, transport_config
    ):
        client = supply_chain_buyer_client
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/transport/config").json() == {"transport": "SLIM"}

        prompts = client.get("/suggested-prompts").json()["supply_chain"]
        assert prompts, "the baseline prompts must be offered"
        assert {p["configuration"] for p in prompts} == {"baseline"}, (
            "with L9 off, no L9 prompt is offered"
        )

    def test_buyer_serves_the_oasf_records(
        self, supply_chain_buyer_client, transport_config
    ):
        client = supply_chain_buyer_client
        ok = client.get("/agents/supply-chain-buyer-agent/oasf")
        assert ok.status_code == 200
        assert client.get("/agents/no-such-agent/oasf").status_code == 404
        assert client.get("/agents/..%2Fmain/oasf").status_code == 404

    def test_buyer_refuses_l9_when_it_is_off(
        self, supply_chain_buyer_client, transport_config
    ):
        resp = supply_chain_buyer_client.post(
            "/agent/prompt",
            json={"prompt": "any", "case": "ambiguous", "configuration": "l9_full"},
        )
        assert resp.status_code == 400
