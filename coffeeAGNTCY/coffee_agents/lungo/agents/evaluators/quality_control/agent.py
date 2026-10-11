# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

from agents.scenario.profiles import farms_mentioned, load_farm_profiles
from common.llm import get_llm
from ioa_observe.sdk.decorators import agent, tool

logger = logging.getLogger("lungo.quality_control_agent.agent")

# Moisture outside this band (percent) risks mold or a flat cup.
_MOISTURE_OK = (10.0, 12.0)


def score_lot(quality: dict) -> tuple[float, str]:
    """Deterministic 0-100 quality score and grade for one lot.

    Kept in plain Python (not the LLM) so the demo scenario is repeatable.
    """
    score = 100.0
    score -= quality["defect_rate_pct"] * 5
    score -= max(0.0, 90.0 - quality["cupping_score"]) * 3
    low, high = _MOISTURE_OK
    moisture = quality["moisture_pct"]
    score -= max(0.0, low - moisture, moisture - high) * 15
    score = round(max(0.0, min(100.0, score)), 1)

    if score >= 80:
        grade = "A"
    elif score >= 60:
        grade = "B"
    elif score >= 45:
        grade = "C"
    else:
        grade = "FAIL"
    return score, grade


@tool(name="quality_report_tool")
def build_quality_report(user_message: str) -> str:
    """Score the requested farms and have the LLM write an inspector's note."""
    profiles = load_farm_profiles()
    lines = []
    for slug in farms_mentioned(user_message, profiles):
        q = profiles[slug]["quality"]
        score, grade = score_lot(q)
        lines.append(
            f"{slug}: score={score} grade={grade} "
            f"(cupping={q['cupping_score']}, defects={q['defect_rate_pct']}%, "
            f"moisture={q['moisture_pct']}%)"
        )
    scores = "\n".join(lines)

    prompt = (
        "You are a strict coffee quality-control inspector. Below are the computed "
        "quality scores for the requested lots. Do NOT change the scores or grades. "
        "Write one short sentence per farm explaining the main quality risk or "
        "strength, then state which lot you would approve from a quality-only view. "
        "You only care about quality, not price or sustainability.\n\n"
        f"Scores:\n{scores}\n\nRequest: {user_message}"
    )
    note = get_llm(streaming=False).invoke(prompt).content.strip()
    logger.info("Quality report scores:\n%s", scores)
    return f"QUALITY SCORES\n{scores}\n\nINSPECTOR NOTE\n{note}"


@agent(name="quality_control_agent")
class QualityControlAgent:
    async def invoke(self, user_message: str) -> str:
        result = build_quality_report(user_message)
        if not result.strip():
            raise RuntimeError("No valid response generated.")
        return result.strip()
