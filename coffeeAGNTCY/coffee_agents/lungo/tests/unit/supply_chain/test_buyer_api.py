# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Buyer HTTP routes: prompts, OASF, explicit-field precedence, NDJSON stream."""

import json

import pytest
from fastapi.testclient import TestClient

from agents.supervisors.supply_chain import main
from agents.supply_chain.common.fixtures import CASES


class FakeRunner:
    l9_enabled = True

    def __init__(self):
        self.calls = []

    async def stream(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        yield {"type": "status", "state": "selected", "case": kwargs["case"]}
        yield {"type": "message", "body": 'It\'s "fine"'}
        yield {"type": "verdict", "verdict": {"verdict": "PASS"}}

    async def run(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        return {"messages": 1}


@pytest.fixture
def client():
    # No ``with``: the lifespan (and its background init) is not started.
    main.app.state.supply_chain_runner = FakeRunner()
    yield TestClient(main.app)
    del main.app.state.supply_chain_runner


def test_routes_report_initializing_before_the_runner_exists():
    if hasattr(main.app.state, "supply_chain_runner"):
        del main.app.state.supply_chain_runner
    c = TestClient(main.app)
    assert c.post("/agent/prompt", json={"prompt": "x"}).status_code == 503
    assert c.post("/agent/prompt/stream", json={"prompt": "x"}).status_code == 503
    assert c.get("/health").json() == {"status": "ok"}


GOALS = {
    "ambiguous": "DR-1",
    "explicit": "CE-1",
    "infeasible": "IE-1",
    "disruption": "CC-4",
}
RUN_TYPES = ("baseline", "l9_hybrid", "l9_full")


def test_with_l9_on_twelve_prompts_are_offered_grouped_by_goal(client):
    prompts = client.get("/suggested-prompts").json()["supply_chain"]

    assert len(prompts) == 12
    assert {(p["case"], p["configuration"]) for p in prompts} == {
        (c, k) for c in CASES for k in RUN_TYPES
    }
    # Grouped by goal, each goal in baseline, hybrid, full order.
    assert [p["goal"] for p in prompts] == [
        g for g in GOALS.values() for _ in RUN_TYPES
    ]
    assert [p["configuration"] for p in prompts[:3]] == list(RUN_TYPES)
    assert all(p["prompt"] and p["description"] for p in prompts)
    assert all(GOALS[p["case"]] == p["goal"] for p in prompts)


def test_every_prompt_tag_equals_its_case_and_configuration(client):
    from agents.supervisors.supply_chain.selection import parse_tag

    for p in client.get("/suggested-prompts").json()["supply_chain"]:
        assert p["prompt"].startswith("I'd like to have a 1,000-tonne coffee shipment")
        assert parse_tag(p["prompt"]) == (p["case"], p["configuration"])


def test_with_l9_off_only_four_baseline_prompts_without_any_l9_mention(client):
    main.app.state.supply_chain_runner.l9_enabled = False
    prompts = client.get("/suggested-prompts").json()["supply_chain"]

    assert len(prompts) == 4
    assert {p["configuration"] for p in prompts} == {"baseline"}
    assert {p["case"] for p in prompts} == set(CASES)
    assert not any("l9" in str(p).lower() for p in prompts)


def test_before_the_runner_exists_no_l9_prompt_is_offered():
    if hasattr(main.app.state, "supply_chain_runner"):
        del main.app.state.supply_chain_runner
    prompts = TestClient(main.app).get("/suggested-prompts").json()["supply_chain"]
    assert len(prompts) == 4 and not any("l9" in str(p).lower() for p in prompts)


def test_transport_config_is_slim(client):
    assert client.get("/transport/config").json() == {"transport": "SLIM"}


def test_oasf_record_is_served_and_unknown_slugs_are_404(client):
    ok = client.get("/agents/supply-chain-buyer-agent/oasf")
    assert ok.status_code == 200 and ok.json()["name"] == "Buyer agent"
    assert client.get("/agents/nope/oasf").status_code == 404
    assert client.get("/agents/..%2Fmain/oasf").status_code == 404


def test_stream_passes_explicit_fields_and_emits_valid_ndjson(client):
    response = client.post(
        "/agent/prompt/stream",
        json={"prompt": "p", "case": "infeasible", "configuration": "l9_hybrid"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    lines = [json.loads(line) for line in response.text.splitlines()]
    assert [line["response"]["type"] for line in lines] == [
        "status",
        "message",
        "verdict",
    ]
    assert lines[1]["response"]["body"] == 'It\'s "fine"'
    assert all(line["session_id"] for line in lines)
    prompt, kwargs = main.app.state.supply_chain_runner.calls[0]
    assert (prompt, kwargs["case"], kwargs["configuration"]) == (
        "p",
        "infeasible",
        "l9_hybrid",
    )


@pytest.mark.parametrize("route", ["/agent/prompt", "/agent/prompt/stream"])
def test_unknown_case_or_configuration_is_a_400_before_any_run(client, route):
    for body in (
        {"prompt": "p", "case": "nope"},
        {"prompt": "p", "configuration": "x"},
    ):
        assert client.post(route, json=body).status_code == 400
    assert main.app.state.supply_chain_runner.calls == []


def test_non_streaming_prompt_returns_the_run_result(client):
    body = client.post("/agent/prompt", json={"prompt": "p", "case": "explicit"}).json()
    assert body["response"] == {"messages": 1} and body["session_id"]


def test_an_error_midstream_becomes_a_json_error_line(client):
    class Broken(FakeRunner):
        async def stream(self, prompt, **kwargs):
            yield {"type": "status", "state": "selected"}
            raise RuntimeError("secret internal detail")

    main.app.state.supply_chain_runner = Broken()
    lines = [
        json.loads(x)
        for x in client.post(
            "/agent/prompt/stream", json={"prompt": "p"}
        ).text.splitlines()
    ]

    assert lines[-1]["response"]["state"] == "error"
    assert "secret internal detail" not in json.dumps(lines)
