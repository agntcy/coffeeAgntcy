# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Group member behavior: noop gate, reply shape, confirmation, run memory."""

import json

import pytest

from agents.supply_chain.common.envelope import Envelope, decode
from agents.supply_chain.common.member import ConfirmDecision, MemberAgent
from tests.helpers.supply_chain_fakes import FakeLLM

PARTIES = ["supplier_a", "supplier_b", "supplier_c", "logistics", "buyer"]


def _request(to, kind="negotiation", **kw) -> Envelope:
    base = dict(
        run_id="r1",
        seq=4,
        sender="moderator",
        to=tuple(to),
        kind=kind,
        case="explicit",
        configuration="baseline",
        body="Please state your position.",
    )
    base.update(kw)
    return Envelope(**base)


@pytest.mark.parametrize("party", PARTIES)
async def test_unaddressed_member_returns_noop_without_calling_llm(party):
    llm = FakeLLM()
    others = [p for p in PARTIES if p != party]
    reply = await MemberAgent(party, llm).handle(_request([others[0]]))
    assert reply.kind == "noop" and llm.calls == []


async def test_own_message_is_ignored():
    llm = FakeLLM()
    agent = MemberAgent("supplier_a", llm)
    reply = await agent.handle(_request(["supplier_a"], sender="supplier_a"))
    assert reply.kind == "noop" and llm.calls == []


async def test_control_message_gets_noop():
    llm = FakeLLM()
    reply = await MemberAgent("buyer", llm).handle(
        _request(["buyer"], kind="control", body="RUN_END")
    )
    assert reply.kind == "noop" and llm.calls == []


async def test_negotiation_reply_is_one_envelope_to_the_moderator():
    llm = FakeLLM("Supplier B's lot is 350 t, ready Nov 15, 09:00 UTC.")
    reply = await MemberAgent("supplier_b", llm).handle(_request(["supplier_b"]))
    assert (reply.kind, reply.to, reply.sender, reply.reply_to) == (
        "negotiation",
        ("moderator",),
        "supplier_b",
        4,
    )
    assert (
        decode(reply.encode()).body
        == "Supplier B's lot is 350 t, ready Nov 15, 09:00 UTC."
    )


async def test_prompt_holds_only_own_slice_and_the_public_transcript():
    llm = FakeLLM("ok")
    transcript = (
        {
            "seq": 2,
            "from": "buyer",
            "to": ["supplier_a"],
            "kind": "negotiation",
            "body": "Need 1,000 t.",
        },
    )
    await MemberAgent("supplier_a", llm).handle(
        _request(["supplier_a"], transcript=transcript)
    )
    prompt = llm.prompt_text()
    assert "400 metric tonnes" in prompt and "Need 1,000 t." in prompt
    assert "350" not in prompt and "19,000" not in prompt and "20,000" not in prompt


async def test_confirm_reply_is_structured_json():
    llm = FakeLLM(ConfirmDecision(decision="reject", reason="Plan ships C late."))
    request = _request(
        ["logistics"], kind="confirm_request", plan_version=2, body="Plan v2"
    )
    reply = await MemberAgent("logistics", llm).handle(request)
    assert reply.kind == "confirm_reply" and reply.plan_version == 2
    assert json.loads(reply.body) == {
        "decision": "reject",
        "reason": "Plan ships C late.",
    }


async def test_ready_time_event_changes_only_that_suppliers_prompt():
    event = _request(
        ["supplier_c"],
        kind="event",
        phase="ready_time_change",
        case="disruption",
        body="Delay.",
    )
    llm_c = FakeLLM("Acknowledged, ready Nov 17.", "Still ready Nov 17.")
    agent_c = MemberAgent("supplier_c", llm_c)
    await agent_c.handle(event)
    assert "November 17, 09:00 UTC" in llm_c.prompt_text(0)
    await agent_c.handle(_request(["supplier_c"], case="disruption", seq=9))
    assert "November 17, 09:00 UTC" in llm_c.prompt_text(1)

    llm_b = FakeLLM("Unaffected.")
    await MemberAgent("supplier_b", llm_b).handle(
        _request(
            ["supplier_b"], kind="event", phase="ready_time_change", case="disruption"
        )
    )
    assert "November 15, 09:00 UTC" in llm_b.prompt_text()


async def test_disruption_flag_is_per_run():
    llm = FakeLLM("a", "b")
    agent = MemberAgent("supplier_c", llm)
    await agent.handle(
        _request(
            ["supplier_c"],
            kind="event",
            phase="ready_time_change",
            case="disruption",
            run_id="r1",
        )
    )
    await agent.handle(_request(["supplier_c"], case="disruption", run_id="r2"))
    assert "November 16, 09:00 UTC" in llm.prompt_text(1)


async def test_unknown_case_is_rejected():
    with pytest.raises(ValueError):
        await MemberAgent("buyer", FakeLLM("x")).handle(
            _request(["buyer"], case="nope")
        )


async def test_role_instructions_do_not_depend_on_the_configuration():
    prompts = []
    for configuration in ("baseline", "l9_hybrid"):
        llm = FakeLLM("ok")
        await MemberAgent("supplier_b", llm).handle(
            _request(["supplier_b"], configuration=configuration)
        )
        prompts.append(llm.prompt_text())
    assert prompts[0] == prompts[1]


async def test_logistics_infeasible_case_has_no_expedited_capacity():
    llm = FakeLLM("No expedited capacity.")
    await MemberAgent("logistics", llm).handle(
        _request(["logistics"], case="infeasible")
    )
    assert (
        "no capacity is available" in llm.prompt_text()
        and "19,000" not in llm.prompt_text()
    )
    llm = FakeLLM("Expedited is possible.")
    await MemberAgent("logistics", llm).handle(_request(["logistics"], case="explicit"))
    assert "19,000" in llm.prompt_text()


async def test_run_memory_is_bounded():
    agent = MemberAgent("buyer", FakeLLM(*["x"] * 40))
    for i in range(40):
        await agent.handle(_request(["buyer"], run_id=f"run-{i}"))
    assert len(agent._runs) == 32
