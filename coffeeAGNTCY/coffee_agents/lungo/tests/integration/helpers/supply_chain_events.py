# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Helpers for the Supply Chain Commitment integration tests."""

from __future__ import annotations

import json
from typing import Any

# A control message (RUN_END) is announced to everyone and asks for no reply.
_NO_REPLY_KINDS = {"control"}


def read_ndjson(text: str) -> list[dict[str, Any]]:
    """The ``response`` object of every line of a streamed run."""
    return [json.loads(line)["response"] for line in text.splitlines() if line.strip()]


def reply_problems(messages: list[dict[str, Any]]) -> list[str]:
    """Describe every step whose addressees did not each reply exactly once.

    A step is a message with no ``reply_to`` and a kind that expects replies.
    Each of its addressees must have sent exactly one message whose
    ``reply_to`` is the step's ``seq``. An empty list means the invariant holds.
    """
    problems: list[str] = []
    for request in messages:
        if request.get("reply_to") is not None:
            continue
        if request.get("kind") in _NO_REPLY_KINDS:
            continue
        replies = [m for m in messages if m.get("reply_to") == request["seq"]]
        for party in request["to"]:
            count = sum(1 for r in replies if r["from"] == party)
            if count != 1:
                problems.append(
                    f"step {request['seq']} ({request['kind']}): "
                    f"{party} replied {count} times"
                )
        for reply in replies:
            if reply["from"] not in request["to"]:
                problems.append(
                    f"step {request['seq']}: unexpected reply from {reply['from']}"
                )
    return problems
