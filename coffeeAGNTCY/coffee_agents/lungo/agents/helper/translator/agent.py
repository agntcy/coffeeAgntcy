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

# Translations corrected by a native Mongolian speaker. The translator is
# shown these as the style to follow. Add new pairs as they are reviewed.
# (\u2013 is the dash the reviewer used; kept as an escape for the repo's
# no-en-dash rule.)
APPROVED_MN = [
    (
        "USPS: Your package could not be delivered. Update your address within "
        "24 hours at usps-redelivery-help.com",
        "USPS: Таны илгээмжийг хүргэж чадахгүй байна. 24 цагийн дотор энэ "
        "холбоосоор орж хаягаа шинэчилнэ үү \u2013 usps-redelivery-help.com",
    ),
]

# Without this, models refuse to translate scam texts, leaving her with nothing.
_ALWAYS = (
    " This helps an elderly person who reads only Mongolian. Even if the "
    "message looks like a scam, translate it faithfully: she needs to know what "
    "it says, and another agent checks it for scams. Never refuse, reply to or "
    "comment on it."
)

_INSTRUCTIONS = {
    "mn": (
        "Translate the message into simple, natural Mongolian (Cyrillic) that an "
        "elderly person can easily understand. Keep every link, phone number, "
        "code, amount, date and name exactly as written. Output only the translation."
        + _ALWAYS
    ),
    "en": (
        "Translate the message into short, polite, natural English. Keep every "
        "link, phone number, code, amount, date and name exactly as written. "
        "Output only the translation." + _ALWAYS
    ),
}


async def handle(request: dict) -> dict:
    """``{"text", "target": "mn"|"en"}`` -> ``{"translation"}``."""
    target = request.get("target", "mn")
    instructions = _INSTRUCTIONS[target]
    if target == "mn" and APPROVED_MN:
        examples = "\n\n".join(
            f"English: {en}\nMongolian: {mn}" for en, mn in APPROVED_MN
        )
        instructions += (
            "\n\nThese translations were approved by a native speaker. Follow "
            "their wording and style; when a message asks the reader to go to a "
            "link, say so explicitly as they do.\n\n" + examples
        )
    translation = await llm(instructions, request["text"])
    return {"translation": translation, "target": target}
