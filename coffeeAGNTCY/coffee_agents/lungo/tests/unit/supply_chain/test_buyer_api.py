# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Buyer HTTP routes: prompts, OASF, explicit-field precedence, NDJSON stream."""

import contextlib
import json

import pytest
from fastapi.testclient import TestClient

from agents.supervisors.supply_chain import main
from agents.supply_chain.common.fixtures import CASES


class FakeRunner:
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


@pytest.mark.parametrize(
    "name, value",
    [
        ("SUPPLY_CHAIN_MAX_ROUNDS", "zero"),
        ("SUPPLY_CHAIN_MAX_ROUNDS", "0"),
    ],
)
def test_bad_setting_stops_start_up(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        with TestClient(main.app):
            pass


GOALS = {
    "ambiguous": "DR-1",
    "explicit": "CE-1",
    "infeasible": "IE-1",
    "disruption": "CC-4",
}


def test_one_baseline_prompt_is_offered_per_goal(client):
    prompts = client.get("/suggested-prompts").json()["supply_chain"]

    assert [(p["case"], p["configuration"]) for p in prompts] == [
        (c, "baseline") for c in CASES
    ]
    assert [p["goal"] for p in prompts] == list(GOALS.values())
    assert all(p["prompt"] and p["description"] for p in prompts)


def test_every_prompt_tag_equals_its_case_and_configuration(client):
    from agents.supervisors.supply_chain.selection import parse_tag

    for p in client.get("/suggested-prompts").json()["supply_chain"]:
        assert parse_tag(p["prompt"]) == (p["case"], p["configuration"])


def test_every_prompt_is_the_exact_opening_the_agents_receive(client):
    """The visible prompt is the Buyer's fixed opening plus the closing tag.

    The agents never read the typed prompt; the case picks their opening. If the
    two differed, the UI would show the user something the agents do not get.
    """
    from agents.supply_chain.common import fixtures as fx

    for p in client.get("/suggested-prompts").json()["supply_chain"]:
        opening = fx.buyer_slice(p["case"]).opening_wording
        assert p["prompt"] == f"{opening} ({p['case']}/{p['configuration']})"


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
    assert lines[-1]["session_id"] == lines[0]["session_id"]
    assert "secret internal detail" not in json.dumps(lines)


def test_the_stream_session_stays_open_until_the_last_event(client, monkeypatch):
    log = []

    @contextlib.contextmanager
    def session_start():
        log.append("start")
        yield {"executionID": "s1"}
        log.append("end")

    class Recording(FakeRunner):
        async def stream(self, prompt, **kwargs):
            for i in range(2):
                log.append(f"event {i}")
                yield {"type": "message", "body": str(i)}

    monkeypatch.setattr(main, "session_start", session_start)
    main.app.state.supply_chain_runner = Recording()
    client.post("/agent/prompt/stream", json={"prompt": "p"})

    assert log == ["start", "event 0", "event 1", "end"]


def test_a_failed_run_does_not_return_the_exception_text(client):
    class Broken(FakeRunner):
        async def run(self, prompt, **kwargs):
            raise RuntimeError("secret internal detail")

    main.app.state.supply_chain_runner = Broken()
    response = client.post("/agent/prompt", json={"prompt": "p"})

    assert response.status_code == 500
    assert "secret internal detail" not in response.text
