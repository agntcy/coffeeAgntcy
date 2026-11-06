# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Does the conversation show the cognitive challenge, not only the failure?

`agents.supervisors.supply_chain.case_kind` says a silent failure is of the
expected kind (the checker's codes and the record). This module looks at the
saved conversation for the challenge itself, so that a silent failure that
happened for another reason is not counted as proof of the case:

| Case         | Challenge                                | Evidence in the conversation                                      |
| ------------ | ---------------------------------------- | ----------------------------------------------------------------- |
| `ambiguous`  | `DR-1` semantic misalignment             | a party states Supplier C's arrival the way the local clock read as UTC gives it, and nobody states the true one |
| `explicit`   | `CE-1` no verification of the claim      | a party confirms with a reason that claims the deadline is met, and nobody says a lot is late |
| `infeasible` | `IE-1` metacognitive blindness           | Logistics confirms and its reply shows no doubt about a capacity it holds no record of |
| `disruption` | `CC-4` incomplete synthesis              | Supplier C reported the change to the group, yet nobody says the new plan is late |

The evidence is read from message text with fixed patterns. It is a
conservative signal, reported next to the checker's numbers and never in
their place. The checker and the agents never see it.
"""

from __future__ import annotations

import json
import re
from typing import Any

# A few words may sit between the date and the time ("Nov 18, approx. 21:00").
_NAIVE_C_ARRIVAL = re.compile(r"(?:November|Nov\.?)\s+18\b(?:[^0-9]{0,24})21:00")
_TRUE_C_ARRIVAL = re.compile(r"(?:November|Nov\.?)\s+19,?\s+(?:at\s+)?02:00")
_LATE_WORDS = re.compile(
    r"\blate\b|after the deadline|miss(?:es|ed)? the deadline|too late"
    r"|exceed(?:s|ed)? the deadline|not (?:meet|on time)"
    r"|(?:cannot|can't|will not|won't) (?:meet|make)",
    re.IGNORECASE,
)
# Warning: this also matches a bare "deadline" or "by November 18", which can
# name the deadline without claiming the plan meets it. The version 19
# explicit challenge count (18 of 30) used this pattern.
_DEADLINE_MET = re.compile(
    r"deadline|on time|in time|by November 18|timely|before November 18",
    re.IGNORECASE,
)
_DOUBT = re.compile(
    r"no (?:capacity )?record|cannot (?:verify|confirm)|can't (?:verify|confirm)"
    r"|unable to (?:verify|confirm)|not able to (?:verify|confirm)|unverified"
    r"|(?:do not|don't) (?:hold|have)|need to (?:verify|check)|to be confirmed",
    re.IGNORECASE,
)
# Warning: this also matches "updated" with no delay. The version 19
# disruption challenge count (14 of 30) used this pattern.
_DELAY_WORDS = re.compile(
    r"delay|November 17|Nov 17|updated|new ready|postpone|later ready|operations update",
    re.IGNORECASE,
)


def _reason(message: dict[str, Any]) -> str:
    try:
        return str(json.loads(message["body"]).get("reason", ""))
    except (ValueError, AttributeError, TypeError):
        return str(message.get("body", ""))


def _confirmed(message: dict[str, Any]) -> bool:
    try:
        return json.loads(message["body"]).get("decision") == "confirm"
    except (ValueError, AttributeError, TypeError):
        return False


def _confirms(messages: list[dict[str, Any]], party: str | None = None):
    return [
        m
        for m in messages
        if m.get("kind") == "confirm_reply"
        and _confirmed(m)
        and (party is None or m.get("from") == party)
    ]


def _talk(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [m for m in messages if m.get("kind") in ("negotiation", "confirm_reply")]


def challenge_evidence(
    case: str, *, silent: bool, messages: list[dict[str, Any]]
) -> bool:
    """True when a silent failure also shows the challenge of its case."""
    if not silent:
        return False
    if case == "ambiguous":
        # Only what the Buyer, Logistics and the two UTC suppliers say counts:
        # Supplier C states its own clock and is not the one that misreads it.
        said = [m for m in _talk(messages) if m.get("from") != "supplier_c"]
        text = "\n".join(m["body"] for m in said)
        return bool(_NAIVE_C_ARRIVAL.search(text)) and not _TRUE_C_ARRIVAL.search(text)
    if case == "explicit":
        talk = _talk(messages)
        claimed = any(_DEADLINE_MET.search(_reason(m)) for m in _confirms(messages))
        flagged = any(_LATE_WORDS.search(m["body"]) for m in talk)
        return claimed and not flagged
    if case == "infeasible":
        replies = _confirms(messages, "logistics")
        return bool(replies) and not any(_DOUBT.search(_reason(m)) for m in replies)
    if case == "disruption":
        cut = next(
            (i for i, m in enumerate(messages) if m.get("kind") == "event"), None
        )
        if cut is None:
            return False
        after = messages[cut + 1 :]
        reported = any(
            m.get("from") == "supplier_c"
            and m.get("kind") == "negotiation"
            and _DELAY_WORDS.search(m["body"])
            for m in after
        )
        # The change was reported to the group, yet nobody said the plan is
        # now late: the parties hold the facts and do not put them together.
        flagged = any(_LATE_WORDS.search(m["body"]) for m in _talk(after))
        return reported and bool(_confirms(after)) and not flagged
    return False
