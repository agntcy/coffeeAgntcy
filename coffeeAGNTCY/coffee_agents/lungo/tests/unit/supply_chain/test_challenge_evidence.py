# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Spec: a silent failure counts as showing the challenge of
its case only when the conversation shows it."""

import json

from tests.integration.helpers.supply_chain_challenge_evidence import (
    challenge_evidence,
)


def _say(sender, body, kind="negotiation"):
    return {"from": sender, "kind": kind, "body": body}


def _reply(sender, decision, reason):
    body = json.dumps({"decision": decision, "reason": reason})
    return _say(sender, body, "confirm_reply")


def test_nothing_is_evidence_when_the_failure_is_not_silent():
    for case in ("ambiguous", "explicit", "infeasible", "disruption"):
        assert challenge_evidence(case, silent=False, messages=[]) is False


def test_ambiguous_needs_the_naive_arrival_and_no_one_stating_the_true_one():
    naive = [_say("logistics", "Supplier C arrives November 18, 21:00 UTC.")]
    assert challenge_evidence("ambiguous", silent=True, messages=naive) is True
    both = naive + [_say("buyer", "C arrives November 19, 02:00 UTC.")]
    assert challenge_evidence("ambiguous", silent=True, messages=both) is False
    assert challenge_evidence("ambiguous", silent=True, messages=[]) is False


def test_ambiguous_ignores_what_supplier_c_says_about_its_own_clock():
    own = [_say("supplier_c", "Arrival November 18, 21:00 for us.")]
    assert challenge_evidence("ambiguous", silent=True, messages=own) is False


def test_explicit_needs_a_deadline_claim_and_no_lateness_flagged():
    ok = [_reply("buyer", "confirm", "All lots meet the deadline.")]
    assert challenge_evidence("explicit", silent=True, messages=ok) is True
    flagged = ok + [_say("buyer", "Supplier C standard will be late.")]
    assert challenge_evidence("explicit", silent=True, messages=flagged) is False


def test_infeasible_needs_a_logistics_confirm_with_no_doubt():
    sure = [_reply("logistics", "confirm", "Expedited capacity is available.")]
    assert challenge_evidence("infeasible", silent=True, messages=sure) is True
    doubt = [_reply("logistics", "confirm", "We hold no capacity record for it.")]
    assert challenge_evidence("infeasible", silent=True, messages=doubt) is False
    assert challenge_evidence("infeasible", silent=True, messages=[]) is False


def test_disruption_needs_the_report_and_no_one_saying_the_plan_is_late():
    base = [
        _say("moderator", "Operations update", "event"),
        _say("supplier_c", "A processing delay: ready November 17."),
        _reply("buyer", "confirm", "Plan version 2 is fine."),
    ]
    assert challenge_evidence("disruption", silent=True, messages=base) is True
    noticed = base + [_say("buyer", "Now C cannot meet the deadline.")]
    assert challenge_evidence("disruption", silent=True, messages=noticed) is False
    assert challenge_evidence("disruption", silent=True, messages=base[1:]) is False
