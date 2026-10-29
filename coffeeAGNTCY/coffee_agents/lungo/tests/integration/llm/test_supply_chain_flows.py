# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""End-to-end Supply Chain Commitment runs against the real model.

These tests never assert PASS. A baseline run may fail, even silently: that is
the finding the use case exists to show. They assert that a run is complete and
well formed: it produced a record and a checker verdict, and every step's
addressees each replied exactly once.
"""

import json
import logging
from pathlib import Path

import pytest
from tests.integration.helpers.supply_chain_events import read_ndjson, reply_problems

logger = logging.getLogger(__name__)

PROMPTS_FILE = (
    Path(__file__).resolve().parents[3]
    / "agents"
    / "supervisors"
    / "supply_chain"
    / "suggested_prompts.json"
)

SUPPLY_CHAIN_AGENTS = [
    "supply-chain-supplier-a",
    "supply-chain-supplier-b",
    "supply-chain-supplier-c",
    "supply-chain-logistics",
]

TRANSPORT_MATRIX = [
    pytest.param(
        {
            "DEFAULT_MESSAGE_TRANSPORT": "SLIM",
            "TRANSPORT_SERVER_ENDPOINT": "http://127.0.0.1:46357",
        },
        id="SLIM",
    )
]

L9_NOT_BUILT = pytest.mark.skip(
    reason="L9 bridge not built yet (tasks 4.4 and 4.5); also needs L9 switched on"
)

# One case per configuration. `ambiguous` is the headline case; `disruption`
# also covers the step where the Moderator announces a change to a party.
FLOW_CASES = [
    pytest.param("ambiguous", "baseline", id="ambiguous-baseline"),
    pytest.param("disruption", "baseline", id="disruption-baseline"),
    pytest.param(
        "ambiguous", "l9_hybrid", id="ambiguous-l9_hybrid", marks=L9_NOT_BUILT
    ),
    pytest.param("ambiguous", "l9_full", id="ambiguous-l9_full", marks=L9_NOT_BUILT),
]


def prompt_for(case: str, configuration: str) -> str:
    prompts = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))[
        "supply_chain_prompts"
    ]
    for p in prompts:
        if p["case"] == case and p["configuration"] == configuration:
            return p["prompt"]
    raise LookupError(f"No suggested prompt for {case}/{configuration}")


@pytest.mark.parametrize("transport_config", TRANSPORT_MATRIX, indirect=True)
class TestSupplyChainFlows:
    @pytest.mark.agents(SUPPLY_CHAIN_AGENTS)
    @pytest.mark.usefixtures("agents_up")
    @pytest.mark.parametrize(("case", "configuration"), FLOW_CASES)
    def test_run_is_complete_and_well_formed(
        self,
        supply_chain_buyer_client,
        transport_config,
        tmp_path,
        case,
        configuration,
    ):
        logger.info(
            f"\n---Test: supply chain {case}/{configuration} with transport {transport_config}---"
        )
        resp = supply_chain_buyer_client.post(
            "/agent/prompt/stream",
            json={
                "prompt": prompt_for(case, configuration),
                "case": case,
                "configuration": configuration,
            },
        )
        assert resp.status_code == 200
        events = read_ndjson(resp.text)

        statuses = [e for e in events if e["type"] == "status"]
        assert not [s for s in statuses if s["state"] == "error"], statuses
        selected = statuses[0]
        assert (selected["state"], selected["case"], selected["configuration"]) == (
            "selected",
            case,
            configuration,
        )

        records = [e for e in events if e["type"] == "record"]
        verdicts = [e for e in events if e["type"] == "verdict"]
        assert len(records) == 1, "exactly one record"
        assert len(verdicts) == 1, "exactly one verdict"
        assert verdicts[0]["verdict"]["verdict"] in {"PASS", "FAIL", "INVALID"}
        assert records[0]["record"]["case"] == case
        assert records[0]["record"]["configuration"] == configuration

        messages = [e for e in events if e["type"] == "message"]
        assert messages, "the group must have exchanged messages"
        assert messages[-1]["kind"] == "control", "the run ends with RUN_END"
        assert reply_problems(messages) == []

        # The fixture points SUPPLY_CHAIN_RUN_DIR at tmp_path / "runs".
        run_dirs = list((tmp_path / "runs").iterdir())
        assert len(run_dirs) == 1, "one run directory per run"
        assert {p.name for p in run_dirs[0].iterdir()} >= {
            "messages.jsonl",
            "record.json",
            "verdict.json",
        }
