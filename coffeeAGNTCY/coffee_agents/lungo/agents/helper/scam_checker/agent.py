# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Scam checker agent: looks for the signs of a scam.

Known red flags are matched in plain code (repeatable), and the LLM gives
its own verdict. The final verdict is the more cautious of the two, and
both are returned so a disagreement between them is visible.
"""

import re

from agents.helper.common import llm, make_card

CARD = make_card(
    agent_id="scam_checker",
    name="Scam Checker Agent",
    description="Rates a message SAFE, SUSPICIOUS or SCAM and lists the red flags.",
    examples=['{"text": "USPS: your package is held, pay $1.99 at ..."}'],
    port=9203,
)

_LEVELS = ["SAFE", "SUSPICIOUS", "SCAM"]

_RED_FLAGS = {
    "link": r"https?://|www\.|\b(?:[\w-]+\.)+[a-z]{2,6}\b",
    "urgency": r"\b(urgent|immediately|within \d+ ?(hours?|days?)|today only|final notice|suspended|locked|expire)",
    "payment": r"\b(pay|payment|fee|\$\d|gift ?card|bitcoin|crypto|wire|zelle|venmo|cash ?app)\b",
    "personal info": r"\b(password|ssn|social security|pin|verify your (account|identity)|login|bank details|card number)\b",
    "prize": r"\b(won|winner|prize|lottery|free gift|reward)\b",
}


# Brands scammers pretend to be, and their real domains. A message that names
# one of these but links somewhere else is impersonating it.
OFFICIAL_DOMAINS = {
    "usps": ("usps.com",),
    "fedex": ("fedex.com",),
    "ups": ("ups.com",),
    "amazon": ("amazon.com",),
    "fastrak": ("bayareafastrak.org",),
    "irs": ("irs.gov",),
    "paypal": ("paypal.com",),
    "apple": ("apple.com",),
    "netflix": ("netflix.com",),
    "chase": ("chase.com",),
    "wells fargo": ("wellsfargo.com",),
    "bank of america": ("bankofamerica.com",),
    "social security": ("ssa.gov",),
    "medicare": ("medicare.gov",),
}

_DOMAIN = re.compile(r"\b((?:[\w-]+\.)+[a-z]{2,6})\b", re.I)


def impersonated_brand(text: str) -> str | None:
    """The brand a message claims to be from while linking to another site."""
    lowered = text.lower()
    domains = [d.lower() for d in _DOMAIN.findall(text)]
    if not domains:
        return None
    for brand, official in OFFICIAL_DOMAINS.items():
        if not re.search(rf"\b{brand}\b", lowered):
            continue
        for domain in domains:
            if not any(domain == o or domain.endswith("." + o) for o in official):
                return brand
    return None


def red_flags(text: str) -> list[str]:
    flags = [name for name, pattern in _RED_FLAGS.items() if re.search(pattern, text, re.I)]
    if impersonated_brand(text):
        flags.append("fake company link")
    return flags


def rule_verdict(flags: list[str]) -> str:
    """A link plus pressure to pay or share details is the classic pattern."""
    if "fake company link" in flags:
        return "SCAM"
    pressure = {"urgency", "payment", "personal info", "prize"} & set(flags)
    if "link" in flags and pressure:
        return "SCAM" if len(pressure) >= 2 else "SUSPICIOUS"
    if len(pressure) >= 2:
        return "SUSPICIOUS"
    return "SAFE"


async def handle(request: dict) -> dict:
    """``{"text"}`` -> ``{"verdict", "red_flags", "rule_verdict", "llm_verdict", "reason"}``."""
    text = request["text"]
    flags = red_flags(text)
    by_rules = rule_verdict(flags)

    judgement = await llm(
        "You protect an elderly person from scams. Rate the message. Reply with JSON: "
        '{"verdict": "SAFE"|"SUSPICIOUS"|"SCAM", "reason": "<one short sentence>"}. '
        "Real companies do not ask for payment or passwords through a link in a text.",
        text,
        as_json=True,
    )
    by_llm = str(judgement.get("verdict", "SUSPICIOUS")).upper()
    if by_llm not in _LEVELS:
        by_llm = "SUSPICIOUS"

    verdict = max(by_rules, by_llm, key=_LEVELS.index)
    return {
        "verdict": verdict,
        "red_flags": flags,
        "rule_verdict": by_rules,
        "llm_verdict": by_llm,
        "reason": judgement.get("reason", ""),
    }
