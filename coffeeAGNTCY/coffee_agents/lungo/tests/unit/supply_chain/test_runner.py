# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Runner: selection event, event order, l9_full rejection, files, cancellation."""

import asyncio
import json

import pytest

from agents.supervisors.supply_chain import runner as runner_module
from agents.supervisors.supply_chain.limits import Limits
from agents.supervisors.supply_chain.outcome import Outcome
from agents.supervisors.supply_chain.runner import _WORKFLOW_NAME, SupplyChainRunner
from agents.supply_chain.common.member import MemberAgent
from common.workflow_context_prop import read_workflow_context
from tests.helpers.supply_chain_fakes import FakeGroupTransport, FakeLLM
from tests.helpers.workflow_names import assert_workflow_name_in_catalog

PARTIES = ["supplier_a", "supplier_b", "supplier_c", "logistics"]


class Stub:
    name = "stub"

    def __init__(self, hang=False):
        self.hang = hang
        self.workflow_name = None
        self.reached = asyncio.Event()

    async def run(self, moderator):
        self.workflow_name = read_workflow_context().workflow_name
        await moderator.step("negotiation", ["supplier_a"], "hello", sender="buyer")
        if self.hang:
            self.reached.set()
            await asyncio.sleep(60)
        return Outcome.withheld("buyer_decision", "stub")


@pytest.fixture
def setup(tmp_path, monkeypatch):
    members = {p: MemberAgent(p, FakeLLM(*[f"{p} reply"] * 10)) for p in PARTIES}
    transport = FakeGroupTransport(members)
    stub = Stub()
    monkeypatch.setattr(runner_module, "get_strategy", lambda cfg, **kw: stub)
    runner = SupplyChainRunner(
        transport,
        buyer=MemberAgent("buyer", FakeLLM()),
        limits=Limits(),
        run_root=tmp_path / "runs",
        llm_factory=FakeLLM(),
    )
    return runner, transport, stub, tmp_path / "runs"


async def _events(runner, **kwargs):
    return [e async for e in runner.stream(kwargs.pop("prompt", "p"), **kwargs)]


async def test_first_event_states_the_selection(setup):
    runner, *_ = setup
    events = await _events(runner, case="explicit", configuration="baseline")

    first = events[0]
    assert (first["type"], first["state"]) == ("status", "selected")
    assert (first["case"], first["configuration"]) == ("explicit", "baseline")
    assert "case explicit" in first["message"]


async def test_event_order_and_run_directory(setup):
    runner, transport, stub, run_root = setup
    events = await _events(runner, case="explicit", configuration="baseline")

    types = [e["type"] for e in events]
    assert types[:2] == ["status", "status"]
    assert [e["state"] for e in events[:2]] == ["selected", "started"]
    assert types[-2:] == ["record", "verdict"]
    assert events[-3]["body"] == "RUN_END"
    run_id = events[1]["run_id"]
    assert {p.name for p in (run_root / run_id).iterdir()} >= {
        "meta.json",
        "messages.jsonl",
        "record.json",
        "verdict.json",
    }
    meta = json.loads((run_root / run_id / "meta.json").read_text())
    assert meta["selection"] == {"case": "request", "configuration": "request"}
    assert meta["prompt"] == "p"


async def test_every_event_is_json_with_apostrophes_intact(setup):
    runner, transport, stub, _ = setup
    transport.members["supplier_a"]._llm_factory = FakeLLM('It\'s "fine"')
    events = await _events(runner, case="explicit", configuration="baseline")

    lines = [json.dumps({"response": e}) for e in events]
    parsed = [json.loads(line)["response"] for line in lines]
    assert any(e.get("body") == 'It\'s "fine"' for e in parsed)


async def test_strategy_runs_inside_the_workflow_context(setup):
    runner, _, stub, _ = setup
    await _events(runner, case="explicit", configuration="baseline")
    assert stub.workflow_name == _WORKFLOW_NAME


async def test_l9_full_is_rejected_without_contacting_any_agent(setup, monkeypatch):
    runner, transport, _, run_root = setup
    monkeypatch.undo()  # use the real registry, which rejects l9_full
    events = await _events(runner, case="explicit", configuration="l9_full")

    assert [(e["type"], e["state"]) for e in events] == [
        ("status", "selected"),
        ("status", "not_implemented"),
    ]
    assert "not implemented" in events[1]["message"]
    assert transport.calls == []
    assert not run_root.exists()


async def test_l9_hybrid_is_rejected_without_contacting_any_agent(setup, monkeypatch):
    runner, transport, _, run_root = setup
    monkeypatch.undo()  # use the real registry, which rejects l9_hybrid
    events = await _events(runner, case="explicit", configuration="l9_hybrid")

    assert [(e["type"], e["state"]) for e in events] == [
        ("status", "selected"),
        ("status", "not_implemented"),
    ]
    assert "l9_hybrid" in events[1]["message"]
    assert "not implemented" in events[1]["message"]
    assert transport.calls == []
    assert not run_root.exists()


async def test_the_l9_full_strategy_refuses_to_run_even_if_called_directly():
    from agents.supervisors.supply_chain.strategies import (
        ConfigurationNotImplemented,
        L9FullStrategy,
        is_implemented,
    )

    with pytest.raises(ConfigurationNotImplemented, match="not implemented"):
        await L9FullStrategy().run(None)
    assert is_implemented("baseline")
    assert not is_implemented("l9_hybrid") and not is_implemented("l9_full")


async def test_unknown_configuration_is_a_value_error(setup):
    runner, *_ = setup
    with pytest.raises(ValueError, match="unknown configuration"):
        await _events(runner, configuration="nope")


async def test_closing_the_stream_cancels_the_run(setup):
    runner, _, stub, run_root = setup
    stub.hang = True
    stream = runner.stream("p", case="explicit", configuration="baseline")
    assert (await anext(stream))["state"] == "selected"
    started = await anext(stream)
    await asyncio.wait_for(stub.reached.wait(), 5)
    await stream.aclose()

    outcome = json.loads((run_root / started["run_id"] / "outcome.json").read_text())
    assert outcome["status"] == "cancelled"


async def test_run_returns_selection_record_and_verdict(setup):
    runner, *_ = setup
    result = await runner.run("p", case="infeasible", configuration="baseline")

    assert result["selected"]["case"] == "infeasible"
    assert result["record"]["status"] == "withheld"
    assert result["verdict"]["verdict"] == "PASS"
    assert result["messages"] >= 3  # request, reply, RUN_END


def test_workflow_name_matches_the_catalog():
    assert_workflow_name_in_catalog(_WORKFLOW_NAME, "supply chain runner")
