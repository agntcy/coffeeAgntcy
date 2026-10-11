# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Translation checker agent: catches translations that changed the meaning.

It never sees how the translation was made. It translates the result back
on its own, then compares that with the original. Hard facts (links,
numbers, codes, amounts) are compared in plain code so the check is
repeatable; only the overall meaning is judged by the LLM.
"""

import re

from agents.helper.common import llm, make_card

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
    "Family words: эмээ = grandma, өвөө = grandpa, ээж = mom, аав = dad, "
    "ач/зээ = grandchild, хүү = son, охин = daughter."
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


async def handle(request: dict) -> dict:
    """``{"original", "translation", "source": "en"|"mn"}`` -> verdict."""
    original = request["original"]
    translation = request["translation"]
    source = request.get("source", "en")

    back = await llm(
        f"Translate this into {_LANG[source]}. Output only the translation. "
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
    verdict = {"none": "OK", "minor": "MINOR", "major": "DRIFT"}[severity]
    return {
        "verdict": verdict,
        "back_translation": back,
        "differences": differences.strip(),
    }
