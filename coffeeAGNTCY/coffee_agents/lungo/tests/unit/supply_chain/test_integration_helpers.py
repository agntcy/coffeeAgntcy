# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""The reply invariant helper that the supply chain LLM flow test relies on."""

import json

from tests.integration.helpers.supply_chain_events import read_ndjson, reply_problems


def _msg(seq, sender, to, kind, reply_to=None):
    return {"seq": seq, "from": sender, "to": to, "kind": kind, "reply_to": reply_to}


def test_a_complete_transcript_has_no_problems():
    messages = [
        _msg(1, "buyer", ["supplier_a"], "negotiation"),
        _msg(2, "supplier_a", ["buyer"], "negotiation", reply_to=1),
        _msg(3, "moderator", ["buyer", "supplier_a"], "confirm_request"),
        _msg(4, "buyer", ["moderator"], "confirm_reply", reply_to=3),
        _msg(5, "supplier_a", ["moderator"], "confirm_reply", reply_to=3),
        _msg(6, "moderator", ["buyer", "supplier_a"], "control"),
    ]
    assert reply_problems(messages) == []


def test_a_missing_reply_is_reported():
    messages = [
        _msg(1, "moderator", ["buyer", "supplier_a"], "confirm_request"),
        _msg(2, "buyer", ["moderator"], "confirm_reply", reply_to=1),
    ]
    assert reply_problems(messages) == [
        "step 1 (confirm_request): supplier_a replied 0 times"
    ]


def test_a_duplicate_reply_is_reported():
    messages = [
        _msg(1, "buyer", ["supplier_a"], "negotiation"),
        _msg(2, "supplier_a", ["buyer"], "negotiation", reply_to=1),
        _msg(3, "supplier_a", ["buyer"], "negotiation", reply_to=1),
    ]
    assert reply_problems(messages) == [
        "step 1 (negotiation): supplier_a replied 2 times"
    ]


def test_a_reply_from_a_party_that_was_not_asked_is_reported():
    messages = [
        _msg(1, "buyer", ["supplier_a"], "negotiation"),
        _msg(2, "supplier_a", ["buyer"], "negotiation", reply_to=1),
        _msg(3, "supplier_b", ["buyer"], "negotiation", reply_to=1),
    ]
    assert reply_problems(messages) == ["step 1: unexpected reply from supplier_b"]


def test_read_ndjson_returns_the_response_objects():
    text = "\n".join(
        json.dumps({"response": {"type": "status", "n": n}, "session_id": "s"})
        for n in (1, 2)
    )
    assert read_ndjson(text + "\n") == [
        {"type": "status", "n": 1},
        {"type": "status", "n": 2},
    ]
