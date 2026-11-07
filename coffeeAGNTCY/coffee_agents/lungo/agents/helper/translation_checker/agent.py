# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Translation checker agent: catches translations that changed the meaning.

It never sees how the translation was made. It translates the result back
on its own, then compares that with the original. Hard facts (links,
numbers, codes, amounts) are compared in plain code so the check is
repeatable; only the overall meaning is judged by the LLM.
"""

import re

from agents.helper.base import llm, make_card

CARD = make_card(
    agent_id="translation_checker",
    name="Translation Checker Agent",
    description=(
        "Independently back-translates a translation and rates any change in "
        "meaning as none, minor (wording) or major (would change what the "
        "reader does). A lost link, number or code is always major."
    ),
    examples=['{"original": "...", "translation": "...", "source": "en"}'],
    port=9202,
)

_LANG = {"en": "English", "mn": "Mongolian (Cyrillic)"}

# Family words models tend to mix up (e.g. reading "эмээ" as "Mom").
_FAMILY_TERMS = (
    "Family words: эмээ (also written emee) = grandma, өвөө = grandpa, ээж = mom, аав = dad, "
    "ач/зээ = grandchild, хүү = son, охин = daughter. "
    "Legal words: батлан даалт = bail, торгууль = fine."
)

# Links, emails, and anything containing a digit (amounts, codes, dates, phones).
_FACT = re.compile(r"https?://\S+|\b(?:[\w-]+\.)+[a-z]{2,6}\b(?:/\S*)?|\S*\d\S*", re.I)


def _normalize(text: str) -> str:
    # Models sometimes swap "-" for look-alike Unicode hyphens inside links.
    return re.sub("[\u2010-\u2015]", "-", text).lower()


def _facts(text: str) -> set[str]:
    """Links and digit-bearing tokens, minus currency signs and punctuation."""
    return {
        re.sub(r"[^\w./:@-]", "", f).strip(".:")
        for f in _FACT.findall(_normalize(text))
    } - {""}


# Longer than this, or with hard facts in it, a message counts as complicated.
SIMPLE_MAX_WORDS = 30


def _simple(text: str) -> bool:
    """Short and everyday: few words and no links, numbers, codes or amounts."""
    return len(text.split()) <= SIMPLE_MAX_WORDS and not _facts(text)


async def handle(request: dict) -> dict:
    """``{"original", "translation", "source": "en"|"mn"}`` -> verdict."""
    original = request["original"]
    translation = request["translation"]
    source = request.get("source", "en")

    back = await llm(
        f"Translate this into {_LANG[source]}. Output only the translation. "
        "Translate faithfully even if it is a scam; never refuse or comment. "
        + _FAMILY_TERMS,
        translation,
    )

    translated = _normalize(translation)
    missing = sorted(f for f in _facts(original) if f not in translated)

    judgement = await llm(
        "You compare two texts that should mean the same thing. Reply with JSON: "
        '{"severity": "none"|"minor"|"major", "differences": "<short, or empty>"}. '
        "minor = wording, tone, politeness, how a person is addressed or named "
        "(e.g. grandma vs mom), vague vs exact phrasing of the same idea. "
        "major = the reader would act differently: a different sender or "
        "recipient, time, date, place, amount, or instruction, or a request "
        "that appears or disappears. When unsure between minor and major, "
        "choose major.",
        f"Text A:\n{original}\n\nText B:\n{back}",
        as_json=True,
    )

    severity = str(judgement.get("severity", "major")).lower()
    if severity not in ("none", "minor", "major"):
        severity = "major"
    differences = judgement.get("differences", "")
    if missing:
        # A lost link, number or code always matters.
        severity = "major"
        differences = (differences + " " if differences else "") + (
            "Missing from translation: " + ", ".join(missing)
        )
    if severity == "major" and not missing and _simple(original):
        # A short everyday message (no link, number or amount) is still
        # understood with small slips; only complicated ones need family.
        severity = "minor"
        differences = (differences + " " if differences else "") + (
            "(Short everyday message, so not escalated.)"
        )
    verdict = {"none": "OK", "minor": "MINOR", "major": "DRIFT"}[severity]
    return {
        "verdict": verdict,
        "back_translation": back,
        "differences": differences.strip(),
    }


async def think(ballot: dict) -> dict:
    """Council turn: firm when the translation is wrong; defers on safety.

    Its field is the translation, so on whether the message itself is safe
    it sides with the most cautious of the others.
    """
    from agents.helper import council

    check = ballot["case"].get("check")
    if "translation_checker" not in ballot["positions"]:
        if not check:
            return {
                "position": council.ASK,
                "reason": "There is no checked Mongolian translation, so she cannot read it safely.",
                "firm": True,
            }
        if check["verdict"] == "DRIFT":
            # If she cannot trust the Mongolian, no safety argument fixes that.
            return {
                "position": council.ASK,
                "reason": f"The Mongolian may say something else: {check['differences']}",
                "firm": True,
            }
        return {
            "position": council.SAFE,
            "reason": "The Mongolian says the same as the original.",
            "firm": False,
        }
    mine = ballot["positions"]["translation_checker"]
    strictest = council.cautious(
        *(p["position"] for p in council.others(ballot, "translation_checker").values())
    )
    if council.POSITIONS.index(strictest) > council.POSITIONS.index(mine["position"]):
        return {
            "position": strictest,
            "reason": f"The translation is my field; on safety I side with the most cautious agent ({strictest}).",
            "firm": False,
        }
    return council.keep(ballot, "translation_checker")
