# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Keeping ACCORD and CONCORD out of a baseline run (design D12).

Two levels: the per-run ``configuration`` and the deployment switch
``SUPPLY_CHAIN_L9_ENABLED``. Both must leave a baseline run with no L9 text,
no protocol tool and no protocol message.
"""

import json

import pytest
from fastapi.testclient import TestClient

from agents.supervisors.supply_chain import main
from agents.supervisors.supply_chain import runner as runner_module
from agents.supervisors.supply_chain.limits import Limits
from agents.supervisors.supply_chain.moderator import Moderator
from agents.supervisors.supply_chain.outcome import Outcome
from agents.supervisors.supply_chain.runner import SupplyChainRunner
from agents.supply_chain.common.envelope import Envelope
from agents.supply_chain.common.member import ConfirmDecision, L9Disabled, MemberAgent
from agents.supply_chain.common.skills import L9_ENV, l9_enabled
from tests.helpers.supply_chain_fakes import FakeGroupTransport, FakeLLM

PARTIES = ["buyer", "supplier_a", "supplier_b", "supplier_c", "logistics"]
SKILL_MARKER = "ACCORD"  # present in every L9 prompt, absent from a baseline one


def _request(kind: str, to=("supplier_a",)) -> Envelope:
    return Envelope(
        run_id="r1",
        seq=3,
        sender="moderator",
        to=tuple(to),
        kind=kind,
        case="ambiguous",
        configuration="l9_hybrid",
        body="Please answer.",
    )


# -- the switch itself ---------------------------------------------------------


@pytest.mark.parametrize("raw", ["true", "TRUE", "1", "yes", "on"])
def test_l9_is_on_for_true_values(raw):
    assert l9_enabled({L9_ENV: raw}) is True


@pytest.mark.parametrize("raw", [None, "", "  "])
def test_l9_is_off_by_default_when_unset_or_empty(raw):
    env = {} if raw is None else {L9_ENV: raw}
    assert l9_enabled(env) is False


@pytest.mark.parametrize("raw", ["false", "False", "0", "no", "off", " off "])
def test_l9_is_off_for_false_values(raw):
    assert l9_enabled({L9_ENV: raw}) is False


@pytest.mark.parametrize("raw", ["flase", "2", "disabled", "maybe"])
def test_a_misspelled_value_stops_start_up_instead_of_leaving_l9_on(raw):
    with pytest.raises(ValueError, match=L9_ENV):
        l9_enabled({L9_ENV: raw})


def test_members_and_the_runner_read_the_switch_at_start_up(monkeypatch, tmp_path):
    monkeypatch.setenv(L9_ENV, "false")
    assert MemberAgent("supplier_a").l9_enabled is False
    runner = SupplyChainRunner(FakeGroupTransport({}), run_root=tmp_path)
    assert runner.l9_enabled is False
    assert runner._buyer.l9_enabled is False

    monkeypatch.setenv(L9_ENV, "nonsense")
    with pytest.raises(ValueError):
        MemberAgent("supplier_a")
    with pytest.raises(ValueError):
        SupplyChainRunner(FakeGroupTransport({}), run_root=tmp_path)


# -- a member with L9 off ------------------------------------------------------


@pytest.mark.parametrize("kind", ["accord_request", "concord_request"])
async def test_member_with_l9_off_refuses_protocol_requests(kind):
    llm = FakeLLM()
    member = MemberAgent("supplier_a", llm, l9=False)

    with pytest.raises(L9Disabled, match=kind):
        await member.handle(_request(kind))

    assert llm.calls == [] and llm.bound_tools == []
    assert member._runs == {}  # no run state was created either


async def test_member_with_l9_off_still_negotiates_and_confirms():
    llm = FakeLLM(
        "Supplier A is ready on Nov 14.",
        ConfirmDecision(decision="confirm", reason="fine"),
    )
    member = MemberAgent("supplier_a", llm, l9=False)

    first = await member.handle(_request("negotiation"))
    second = await member.handle(_request("confirm_request"))

    assert first.kind == "negotiation" and second.kind == "confirm_reply"
    assert llm.bound_tools == []
    assert SKILL_MARKER not in llm.prompt_text(0) + llm.prompt_text(1)


async def test_the_refusal_comes_after_the_addressing_gate():
    llm = FakeLLM()
    member = MemberAgent("supplier_a", llm, l9=False)
    reply = await member.handle(_request("accord_request", to=("supplier_b",)))
    assert reply.kind == "noop"


@pytest.mark.parametrize("kind", ["accord_request", "concord_request"])
async def test_member_with_l9_on_still_refuses_protocol_requests(kind):
    llm = FakeLLM()
    member = MemberAgent("supplier_a", llm, l9=True)

    with pytest.raises(L9Disabled, match="not implemented"):
        await member.handle(_request(kind))

    assert llm.calls == [] and llm.bound_tools == []


# -- a baseline run contains no L9 ---------------------------------------------


async def test_a_baseline_run_has_no_l9_text_tool_or_message(tmp_path):
    llms = {p: FakeLLM(*[f"{p} says hello"] * 10) for p in PARTIES}
    for llm in llms.values():
        llm.replies.insert(0, ConfirmDecision(decision="confirm", reason="ok"))
    members = {p: MemberAgent(p, llms[p], l9=True) for p in PARTIES}
    run_dir = tmp_path / "run1"
    moderator = Moderator(
        run_id="run1",
        case="ambiguous",
        configuration="baseline",
        transport=FakeGroupTransport(
            {p: m for p, m in members.items() if p != "buyer"}
        ),
        buyer=members["buyer"],
        limits=Limits(),
        run_dir=run_dir,
    )

    async def baseline_like(mod):
        for party in PARTIES[1:]:
            await mod.step(
                "negotiation", [party], "State your position.", sender="buyer"
            )
        await mod.step("confirm_request", PARTIES, "Confirm version 1?", plan_version=1)
        return Outcome.withheld("buyer_decision", "scripted")

    class Scripted:
        name = "baseline-like"

        async def run(self, mod):
            return await baseline_like(mod)

    await moderator.run(Scripted())

    kinds = {
        json.loads(line)["kind"]
        for line in (run_dir / "messages.jsonl").read_text().splitlines()
    }
    assert not {k for k in kinds if k.startswith(("accord", "concord"))}
    for llm in llms.values():
        assert llm.bound_tools == []
        assert llm.calls, "every agent should have been asked something"
        for index in range(len(llm.calls)):
            assert SKILL_MARKER not in llm.prompt_text(index)
            assert "concord_forge" not in llm.prompt_text(index)


# -- the Buyer with L9 off ------------------------------------------------------


class Stub:
    name = "stub"

    async def run(self, moderator):
        return Outcome.withheld("buyer_decision", "stub")


def _runner(tmp_path, *, l9: bool):
    transport = FakeGroupTransport({})
    runner = SupplyChainRunner(
        transport,
        buyer=MemberAgent("buyer", FakeLLM(), l9=l9),
        run_root=tmp_path / "runs",
        llm_factory=FakeLLM(),
        l9=l9,
    )
    return runner, transport


async def _events(runner, **kwargs):
    return [e async for e in runner.stream("p", **kwargs)]


@pytest.mark.parametrize("configuration", ["l9_hybrid", "l9_full"])
async def test_l9_run_is_refused_without_contacting_any_agent(tmp_path, configuration):
    runner, transport = _runner(tmp_path, l9=False)
    events = await _events(runner, case="ambiguous", configuration=configuration)

    assert [(e["type"], e["state"]) for e in events] == [
        ("status", "selected"),
        ("status", "l9_disabled"),
    ]
    assert "disabled" in events[1]["message"]
    assert transport.calls == []
    assert not (tmp_path / "runs").exists()


async def test_a_prompt_that_asks_for_l9_is_refused_the_same_way(tmp_path):
    from agents.supervisors.supply_chain.selection import _Extracted

    class Reads:
        def __call__(self, **_):
            return self

        def with_structured_output(self, _schema):
            return self

        async def ainvoke(self, _messages):
            return _Extracted(configuration="l9_hybrid")

    runner = SupplyChainRunner(
        FakeGroupTransport({}),
        buyer=MemberAgent("buyer", FakeLLM(), l9=False),
        run_root=tmp_path / "runs",
        llm_factory=Reads(),
        l9=False,
    )
    events = await _events(runner, case="ambiguous")
    assert events[0]["configuration"] == "l9_hybrid"
    assert events[1]["state"] == "l9_disabled"


async def test_run_summary_reports_the_refusal(tmp_path):
    runner, _ = _runner(tmp_path, l9=False)
    result = await runner.run("p", case="ambiguous", configuration="l9_hybrid")
    assert result["l9_disabled"]["state"] == "l9_disabled"
    assert "record" not in result


async def test_baseline_runs_with_l9_off_and_says_so_in_meta(tmp_path, monkeypatch):
    monkeypatch.setattr(runner_module, "get_strategy", lambda cfg, **kw: Stub())
    runner, _ = _runner(tmp_path, l9=False)
    events = await _events(runner, case="ambiguous", configuration="baseline")

    run_id = events[1]["run_id"]
    meta = json.loads((tmp_path / "runs" / run_id / "meta.json").read_text())
    assert meta["l9_available"] is False and meta["configuration"] == "baseline"
    assert events[-1]["type"] == "verdict"


@pytest.mark.parametrize("configuration", ["baseline", "l9_hybrid"])
async def test_both_configurations_run_in_one_deployment_with_l9_on(
    tmp_path, monkeypatch, configuration
):
    monkeypatch.setattr(runner_module, "get_strategy", lambda cfg, **kw: Stub())
    runner, _ = _runner(tmp_path, l9=True)
    events = await _events(runner, case="ambiguous", configuration=configuration)

    meta = json.loads(
        (tmp_path / "runs" / events[1]["run_id"] / "meta.json").read_text()
    )
    assert meta["l9_available"] is True and meta["configuration"] == configuration


# -- the Buyer API -------------------------------------------------------------


class FakeApiRunner:
    def __init__(self, l9: bool):
        self.l9_enabled = l9
        self.calls = []

    async def stream(self, prompt, **kwargs):
        self.calls.append(kwargs)
        yield {"type": "status", "state": "selected"}

    async def run(self, prompt, **kwargs):
        self.calls.append(kwargs)
        return {"messages": 0}


@pytest.fixture
def api():
    runner = FakeApiRunner(l9=False)
    main.app.state.supply_chain_runner = runner
    yield TestClient(main.app), runner
    del main.app.state.supply_chain_runner


@pytest.mark.parametrize("route", ["/agent/prompt", "/agent/prompt/stream"])
def test_an_explicit_l9_request_is_a_400_when_l9_is_off(api, route):
    client, runner = api
    response = client.post(
        route, json={"prompt": "p", "case": "ambiguous", "configuration": "l9_hybrid"}
    )
    assert response.status_code == 400
    assert "SUPPLY_CHAIN_L9_ENABLED" in response.json()["detail"]
    assert runner.calls == []


@pytest.mark.parametrize("route", ["/agent/prompt", "/agent/prompt/stream"])
def test_a_baseline_request_is_accepted_when_l9_is_off(api, route):
    client, runner = api
    response = client.post(
        route, json={"prompt": "p", "case": "ambiguous", "configuration": "baseline"}
    )
    assert response.status_code == 200
    assert runner.calls[0]["configuration"] == "baseline"
