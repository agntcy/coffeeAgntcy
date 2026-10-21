# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Advisor agent: says what a message means and what to do about it.

It works on its own, without seeing the scam checker's verdict, so that
the two can genuinely disagree (e.g. the advisor says "update your address
at the link" while the scam checker says the link is a scam).
"""

from agents.helper.base import llm, make_card

CARD = make_card(
    agent_id="advisor",
    name="Advisor Agent",
    description=(
        "Explains a message in one sentence, suggests what to do, and tags its "
        "topic (health, money, delivery, general)."
    ),
    examples=['{"text": "Your prescription is ready for pickup at CVS."}'],
    port=9204,
)

TOPICS = {"health", "money", "delivery", "general"}


async def handle(request: dict) -> dict:
    """``{"text"}`` -> ``{"summary", "action", "topic", "follows_link"}``."""
    result = await llm(
        "You help an elderly person who does not read English understand a message "
        "they received on their phone or by email. Reply with JSON: "
        '{"summary": "<what the message says, one simple sentence>", '
        '"action": "<what they should do next, one simple sentence>", '
        '"topic": "health"|"money"|"delivery"|"general", '
        '"follows_link": true|false}. '
        "follows_link is true if your suggested action involves opening a link, "
        "calling a number, or paying.",
        request["text"],
        as_json=True,
    )
    topic = str(result.get("topic", "general")).lower()
    return {
        "summary": result.get("summary", ""),
        "action": result.get("action", ""),
        "topic": topic if topic in TOPICS else "general",
        "follows_link": bool(result.get("follows_link")),
    }


async def think(ballot: dict) -> dict:
    """Council turn: starts from its own advice and can be talked out of it."""
    from agents.helper import council

    if "advisor" in ballot["positions"]:
        if not council.disagrees(ballot, "advisor"):
            return council.keep(ballot, "advisor")
        return await council.reconsider(
            "advisor",
            "advisor (you want her to be able to act on her messages)",
            ballot,
        )
    advice = ballot["case"].get("advice") or await handle(
        {"text": ballot["case"]["text"]}
    )
    return {
        "position": council.SAFE,
        "reason": f"My advice: {advice['action']}",
        "firm": False,
    }
