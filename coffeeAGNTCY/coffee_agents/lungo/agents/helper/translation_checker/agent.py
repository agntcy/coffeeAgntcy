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
        "Independently back-translates a translation and reports whether the "
        "meaning or any hard fact (link, number, code, amount) changed."
    ),
    examples=['{"original": "...", "translation": "...", "source": "en"}'],
    port=9202,
)

_LANG = {"en": "English", "mn": "Mongolian (Cyrillic)"}

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
        f"Translate this into {_LANG[source]}. Output only the translation.",
        translation,
    )

    translated = _normalize(translation)
    missing = sorted(f for f in _facts(original) if f not in translated)

    judgement = await llm(
        "You compare two texts that should mean the same thing. Reply with JSON: "
        '{"same_meaning": true|false, "differences": "<short description, or empty>"}. '
        "Ignore wording and style; only flag changes a reader would act on "
        "differently (who, what, when, how much, what to do).",
        f"Text A:\n{original}\n\nText B:\n{back}",
        as_json=True,
    )

    same = bool(judgement.get("same_meaning")) and not missing
    differences = judgement.get("differences", "")
    if missing:
        differences = (differences + " " if differences else "") + (
            "Missing from translation: " + ", ".join(missing)
        )
    return {
        "verdict": "OK" if same else "DRIFT",
        "back_translation": back,
        "differences": differences.strip(),
    }
