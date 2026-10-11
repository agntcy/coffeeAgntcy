# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Translator agent: English <-> Mongolian, written for an elderly reader."""

from agents.helper.common import llm, make_card

CARD = make_card(
    agent_id="translator",
    name="Translator Agent",
    description="Translates between English and simple, natural Mongolian (Cyrillic).",
    examples=['{"text": "Your package has arrived.", "target": "mn"}'],
    port=9201,
)

_INSTRUCTIONS = {
    "mn": (
        "Translate the message into simple, natural Mongolian (Cyrillic) that an "
        "elderly person can easily understand. Keep every link, phone number, "
        "code, amount, date and name exactly as written. Output only the translation."
    ),
    "en": (
        "Translate the message into short, polite, natural English. Keep every "
        "link, phone number, code, amount, date and name exactly as written. "
        "Output only the translation."
    ),
}


async def handle(request: dict) -> dict:
    """``{"text", "target": "mn"|"en"}`` -> ``{"translation"}``."""
    target = request.get("target", "mn")
    translation = await llm(_INSTRUCTIONS[target], request["text"])
    return {"translation": translation, "target": target}
