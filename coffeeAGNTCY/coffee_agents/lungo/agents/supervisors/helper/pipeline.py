# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""How Grandma Helper decides what to tell her.

Several agents look at the same message independently. The supervisor does
not ask an LLM who is right; it applies fixed rules (below) so the same
message always gets the same verdict:

- Red line: a message the scam checker rates SCAM is "danger", whatever
  any other agent says. She is told not to click, pay or reply.
- Disagreement: if agents disagree (the advisor suggests acting on a link
  the scam checker distrusts, or the translation checker says the meaning
  changed), the app does not guess. It says "check with family".
- Failure: if an agent is down, its safety check is missing, so the
  answer can never be "safe"; the app says "check with family".

"Check with family" for a safety reason means "do nothing yet". When only
the translation is in doubt, she still gets the advice, with a warning
that the wording may be off.

Anything that is not plainly safe raises an alert for the family.
"""

import asyncio
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from agents.helper.advisor.agent import CARD as ADVISOR
from agents.helper.scam_checker.agent import CARD as SCAM_CHECKER
from agents.helper.translation_checker.agent import CARD as TRANSLATION_CHECKER
from agents.helper.translator.agent import CARD as TRANSLATOR
from agents.supervisors.helper.agents_client import AgentUnavailable, call_agent

logger = logging.getLogger("helper.supervisor.pipeline")

SAFE, CHECK, DANGER = "safe", "check_with_family", "danger"
_RANK = [SAFE, CHECK, DANGER]

# Fixed Mongolian text, so the most important words never depend on the LLM.
HEADLINE_MN = {
    SAFE: "✅ Энэ мессеж аюулгүй байна.",
    CHECK: "⚠️ Итгэлтэй биш байна. Гэр бүлээсээ асуугаарай.",
    DANGER: "🛑 Энэ бол залилан байж магадгүй!",
}
# Wording approved by a native speaker.
DANGER_ACTION_MN = (
    "Холбоос дээр бүү дар, мөнгө бүү төл, хариу бүү бич. "
    "Таны гэр бүлд бас анхаарууллаа."
)
CHECK_ACTION_MN = "Юу ч бүү хий. Гэр бүлдээ мэдэгдсэн, тэд тусална."
TRANSLATION_UNSURE_HEADLINE_MN = "⚠️ Орчуулга бүрэн зөв биш байж магадгүй."
TRANSLATION_UNSURE_NOTE_MN = "Гэр бүлдээ мэдэгдсэн, тэд шалгаж өгнө."
REPLY_UNSURE_MN = "⚠️ Англи орчуулга буруу байж магадгүй. Илгээхээсээ өмнө гэр бүлээсээ асуугаарай."
REPLY_OK_MN = "✅ Орчуулга зөв байна. Илгээж болно."


@dataclass
class Verdict:
    status: str = SAFE
    reasons: list[str] = field(default_factory=list)
    disagreements: list[str] = field(default_factory=list)
    # True when the doubt is about safety, not just the wording.
    safety_concern: bool = False

    def raise_to(self, status: str, reason: str, *, safety: bool = True) -> None:
        if _RANK.index(status) > _RANK.index(self.status):
            self.status = status
        self.safety_concern = self.safety_concern or safety
        self.reasons.append(reason)


# In-memory family inbox, newest first. Enough for a demo.
FAMILY_ALERTS: list[dict] = []


async def _ask(card, payload: dict, opinions: dict, key: str) -> dict | None:
    """Call one agent, recording its answer (or that it was down) in ``opinions``."""
    try:
        result = await call_agent(card, payload)
    except AgentUnavailable as e:
        opinions[key] = {"error": str(e)}
        return None
    opinions[key] = result
    return result


def _alert_family(kind: str, text: str, verdict: Verdict) -> None:
    FAMILY_ALERTS.insert(
        0,
        {
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "kind": kind,
            "status": verdict.status,
            "message": text,
            "reasons": verdict.reasons,
            "disagreements": verdict.disagreements,
        },
    )
    del FAMILY_ALERTS[50:]


async def explain(text: str) -> dict:
    """An English message she received: what it says, is it safe, what to do."""
    opinions: dict[str, dict] = {}

    # Round 1: three independent opinions on the original message.
    translation, scam, advice = await asyncio.gather(
        _ask(TRANSLATOR, {"text": text, "target": "mn"}, opinions, "translator"),
        _ask(SCAM_CHECKER, {"text": text}, opinions, "scam_checker"),
        _ask(ADVISOR, {"text": text}, opinions, "advisor"),
    )
    translation_mn = (translation or {}).get("translation")

    # Round 2: check the translation; put the advice into Mongolian.
    advice_en = ""
    if advice:
        advice_en = f"{advice['summary']}\n{advice['action']}"
    check, advice_mn = await asyncio.gather(
        _ask(
            TRANSLATION_CHECKER,
            {"original": text, "translation": translation_mn, "source": "en"},
            opinions,
            "translation_checker",
        )
        if translation_mn
        else asyncio.sleep(0),
        _ask(TRANSLATOR, {"text": advice_en, "target": "mn"}, {}, "advice")
        if advice_en
        else asyncio.sleep(0),
    )

    verdict = Verdict()

    # Red line: scams.
    if scam is None:
        verdict.raise_to(CHECK, "The scam checker is down, so safety was not checked.")
    elif scam["verdict"] == "SCAM":
        verdict.raise_to(DANGER, f"Scam checker: SCAM ({', '.join(scam['red_flags']) or scam['reason']}).")
    elif scam["verdict"] == "SUSPICIOUS":
        verdict.raise_to(CHECK, f"Scam checker: suspicious ({scam['reason']}).")
    if scam and scam["rule_verdict"] != scam["llm_verdict"]:
        verdict.disagreements.append(
            f"Scam checker's rules said {scam['rule_verdict']}, its AI said "
            f"{scam['llm_verdict']}; the more cautious answer was used."
        )

    # Disagreement: advisor wants her to act on something the scam checker distrusts.
    if advice and scam and advice["follows_link"] and scam["verdict"] != "SAFE":
        verdict.disagreements.append(
            f"Advisor suggested: \"{advice['action']}\" but the scam checker rated "
            f"the message {scam['verdict']}. The advice was withheld."
        )
        verdict.raise_to(CHECK, "Advisor and scam checker disagree.")

    # Disagreement: translation changed the meaning.
    if translation is None:
        verdict.raise_to(CHECK, "The translator is down, so she cannot read it.")
    elif check is None:
        verdict.raise_to(
            CHECK, "The translation could not be double-checked.", safety=False
        )
    elif check["verdict"] == "DRIFT":
        verdict.disagreements.append(
            f"Translation checker: meaning may have changed ({check['differences']})."
        )
        verdict.raise_to(CHECK, "The translation may be wrong.", safety=False)

    if advice is None:
        verdict.raise_to(CHECK, "The advisor is down.")

    # What she sees, in Mongolian.
    headline = HEADLINE_MN[verdict.status]
    action_mn = (advice_mn or {}).get("translation", "")
    if verdict.status == DANGER:
        action_mn = DANGER_ACTION_MN
    elif verdict.status == CHECK and verdict.safety_concern:
        action_mn = CHECK_ACTION_MN
    elif verdict.status == CHECK:
        headline = TRANSLATION_UNSURE_HEADLINE_MN
        action_mn = f"{action_mn}\n{TRANSLATION_UNSURE_NOTE_MN}".strip()

    if verdict.status != SAFE:
        _alert_family("message", text, verdict)

    return {
        "status": verdict.status,
        "grandma": {
            "headline": headline,
            "translation": translation_mn,
            "advice": action_mn,
        },
        "family": asdict(verdict),
        "agents": opinions,
    }


async def reply(text_mn: str) -> dict:
    """Her reply in Mongolian (e.g. to a delivery customer), put into English."""
    opinions: dict[str, dict] = {}
    translation = await _ask(
        TRANSLATOR, {"text": text_mn, "target": "en"}, opinions, "translator"
    )
    english = (translation or {}).get("translation")
    check = None
    if english:
        check = await _ask(
            TRANSLATION_CHECKER,
            {"original": text_mn, "translation": english, "source": "mn"},
            opinions,
            "translation_checker",
        )

    verdict = Verdict()
    if english is None:
        verdict.raise_to(CHECK, "The translator is down.")
    elif check is None:
        verdict.raise_to(CHECK, "The translation could not be double-checked.")
    elif check["verdict"] == "DRIFT":
        verdict.disagreements.append(
            f"Translation checker: meaning may have changed ({check['differences']})."
        )
        verdict.raise_to(CHECK, "The English may not say what she meant.")

    if verdict.status != SAFE:
        _alert_family("reply", text_mn, verdict)

    return {
        "status": verdict.status,
        "english": english,
        "grandma": {"headline": REPLY_OK_MN if verdict.status == SAFE else REPLY_UNSURE_MN},
        "family": asdict(verdict),
        "agents": opinions,
    }
