# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""The safety council: three agents negotiate a verdict with no one in charge.

The scam checker, the advisor and the translation checker each hold a
position on what she should do with a message:

- SAFE: she can follow the advice.
- ASK_FAMILY: she should wait for family.
- DANGER: she should not click, pay or reply.

A "ballot" travels around the ring, agent to agent, over SLIM. On its turn
an agent reads the others' positions and reasons and keeps or changes its
own. In lap 1 every agent states its first position; from lap 2 an agent
that disagrees with someone reconsiders (with its LLM, unless its position
is firm). The council ends as soon as every reachable agent agrees, or
after ``MAX_LAPS``. Every agent applies the same settling rule (below), so
the outcome comes from the agents, not from the supervisor, which only
hands the first agent the ballot and reads the result.

A position can be "firm": an agent's hard evidence in its own field (the
scam checker's rules found a scam; the translation changed the meaning).
Firm positions are not argued away.

If the next agent does not answer, the sender marks it unreachable and
passes the ballot to the one after; with fewer than two agents left the
council cannot agree and the answer is ASK_FAMILY.
"""

import importlib
import logging
import time
from collections import Counter

from agents.helper.client import AgentUnavailable, call_agent

logger = logging.getLogger("helper.council")

SAFE, ASK, DANGER = "SAFE", "ASK_FAMILY", "DANGER"
POSITIONS = [SAFE, ASK, DANGER]
RING = ["scam_checker", "advisor", "translation_checker"]
MAX_LAPS = 3
# A peer gets this long to show it is alive before the ballot skips it.
PING_SECONDS = 6.0


def cautious(*positions: str) -> str:
    return max(positions, key=POSITIONS.index)


def new_ballot(case: dict, budget_seconds: float) -> dict:
    """The ballot the supervisor hands to the first agent of the ring."""
    return {
        "case": case,
        "ring": list(RING),
        "unreachable": [],
        "positions": {},
        "transcript": [],
        "lap": 1,
        "outcome": None,
        "deadline": time.time() + budget_seconds,
    }


def _active(ballot: dict) -> list[str]:
    return [a for a in ballot["ring"] if a not in ballot["unreachable"]]


def settle(ballot: dict, me: str) -> dict | None:
    """The shared rule every agent applies after its turn.

    Without the scam checker nobody checked for a scam, so the council can
    never call the message safe.
    """
    outcome = _settle(ballot, me)
    if (
        outcome
        and outcome["decision"] == SAFE
        and "scam_checker" in ballot["unreachable"]
    ):
        return {
            "decision": ASK,
            "how": "scam checker unreachable, so safety was not checked",
            "lap": outcome["lap"],
        }
    return outcome


def _settle(ballot: dict, me: str) -> dict | None:
    active = _active(ballot)
    positions = {a: ballot["positions"][a] for a in active if a in ballot["positions"]}
    if len(active) < 2:
        return {
            "decision": ASK,
            "how": "too few agents reachable to agree",
            "lap": ballot["lap"],
        }
    if len(positions) == len(active):
        values = {p["position"] for p in positions.values()}
        if len(values) == 1:
            return {"decision": values.pop(), "how": "consensus", "lap": ballot["lap"]}
    last_turn = me == active[-1]
    if ballot["lap"] >= MAX_LAPS and last_turn:
        counts = Counter(p["position"] for p in positions.values())
        top, n = counts.most_common(1)[0]
        majority = top if n * 2 > len(positions) else ASK
        firm = [p["position"] for p in positions.values() if p.get("firm")]
        decision = cautious(majority, *firm)
        how = "majority" if decision == majority else "firm red line over majority"
        if n * 2 <= len(positions) and decision == ASK:
            how = "no majority"
        return {"decision": decision, "how": how, "lap": ballot["lap"]}
    return None


def others(ballot: dict, me: str) -> dict:
    return {a: p for a, p in ballot["positions"].items() if a != me}


def disagrees(ballot: dict, me: str) -> bool:
    mine = ballot["positions"].get(me, {}).get("position")
    return any(p["position"] != mine for p in others(ballot, me).values())


def describe_others(ballot: dict, me: str) -> str:
    return "\n".join(
        f"- {a}: {p['position']}{' (firm)' if p.get('firm') else ''}: {p['reason']}"
        for a, p in others(ballot, me).items()
    )


def _card(agent_id: str):
    return importlib.import_module(f"agents.helper.{agent_id}.agent").CARD


async def step(me: str, ballot: dict, think) -> dict:
    """One turn for agent ``me``: update its position, then settle or pass on.

    ``think(ballot)`` returns ``{"position", "reason", "firm"}``.
    """
    before = ballot["positions"].get(me, {}).get("position")
    mine = await think(ballot)
    if mine["position"] not in POSITIONS:
        mine["position"] = ASK
    ballot["positions"][me] = {**mine, "lap": ballot["lap"]}
    ballot["transcript"].append(
        {
            "lap": ballot["lap"],
            "agent": me,
            "position": mine["position"],
            "reason": mine["reason"],
            "firm": bool(mine.get("firm")),
            "changed_from": before if before and before != mine["position"] else None,
        }
    )

    outcome = settle(ballot, me)
    if outcome:
        ballot["outcome"] = outcome
        return ballot

    # Pass the ballot to the next reachable agent in the ring.
    while True:
        active = _active(ballot)
        nxt = active[(active.index(me) + 1) % len(active)]
        if nxt == me:
            ballot["outcome"] = settle(ballot, me) or {
                "decision": ASK,
                "how": "too few agents reachable to agree",
                "lap": ballot["lap"],
            }
            return ballot
        if active.index(nxt) == 0:
            ballot["lap"] += 1
        remaining = ballot["deadline"] - time.time()
        try:
            # Check the peer is alive first: a dead peer would otherwise hold
            # the ballot until the whole council runs out of time.
            await call_agent(
                _card(nxt),
                {"ping": True},
                caller=f"{me}_council",
                deadline=min(PING_SECONDS, remaining),
            )
            return await call_agent(
                _card(nxt),
                {"ballot": ballot},
                caller=f"{me}_council",
                deadline=max(remaining, 1.0),
            )
        except AgentUnavailable as e:
            if active.index(nxt) == 0:
                ballot["lap"] -= 1
            logger.warning("%s: %s is unreachable, skipping it (%s)", me, nxt, e)
            ballot["unreachable"].append(nxt)
            ballot["transcript"].append(
                {"lap": ballot["lap"], "agent": nxt, "unreachable": True}
            )
            if len(_active(ballot)) < 2:
                ballot["outcome"] = settle(ballot, me)
                return ballot


async def reconsider(me: str, role: str, ballot: dict) -> dict:
    """Ask this agent's LLM whether the others' reasons change its mind."""
    from agents.helper.base import llm

    current = ballot["positions"][me]
    answer = await llm(
        f"You are the {role} on a council of three AI agents deciding what an "
        "elderly woman who reads only Mongolian should do with a message she "
        "received. Positions: SAFE (she can follow the advice), ASK_FAMILY (she "
        "should wait for her family), DANGER (she must not click, pay or reply). "
        "Read the other agents' positions. Change yours only if their reasons show "
        "something you missed; a firm position rests on hard evidence. Reply with "
        'JSON: {"position": "SAFE"|"ASK_FAMILY"|"DANGER", "reason": "<one short '
        'sentence; if you changed your mind, say why>"}.',
        f"Message:\n{ballot['case']['text']}\n\n"
        f"Your position: {current['position']}: {current['reason']}\n\n"
        f"The others:\n{describe_others(ballot, me)}",
        as_json=True,
    )
    position = str(answer.get("position", ASK)).upper()
    return {
        "position": position if position in POSITIONS else ASK,
        "reason": answer.get("reason", ""),
        "firm": False,
    }


def keep(ballot: dict, me: str) -> dict:
    current = ballot["positions"][me]
    return {k: current[k] for k in ("position", "reason", "firm")}
