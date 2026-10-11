# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

from agents.scenario.profiles import farms_mentioned, load_farm_profiles
from common.llm import get_llm
from ioa_observe.sdk.decorators import agent, tool

logger = logging.getLogger("lungo.sustainability_agent.agent")

# Points lost per risk level for deforestation and water use.
_DEFORESTATION_PENALTY = {"low": 0, "medium": 15, "high": 30}
_WATER_PENALTY = {"low": 0, "medium": 5, "high": 15}


def score_farm(sustainability: dict) -> tuple[float, str]:
    """Deterministic 0-100 sustainability score and grade for one farm.

    Kept in plain Python (not the LLM) so the demo scenario is repeatable.
    """
    score = 60.0
    score += len(sustainability["certifications"]) * 10
    score -= _DEFORESTATION_PENALTY[sustainability["deforestation_risk"]]
    score -= _WATER_PENALTY[sustainability["water_use"]]
    score -= sustainability["shipping_co2_kg_per_lb"] * 10
    score = round(max(0.0, min(100.0, score)), 1)

    if score >= 65:
        grade = "A"
    elif score >= 45:
        grade = "B"
    elif score >= 30:
        grade = "C"
    else:
        grade = "FAIL"
    return score, grade


@tool(name="sustainability_report_tool")
def build_sustainability_report(user_message: str) -> str:
    """Score the requested farms and have the LLM write an auditor's note."""
    profiles = load_farm_profiles()
    lines = []
    for slug in farms_mentioned(user_message, profiles):
        s = profiles[slug]["sustainability"]
        score, grade = score_farm(s)
        certs = ", ".join(s["certifications"]) or "none"
        lines.append(
            f"{slug}: score={score} grade={grade} "
            f"(certifications={certs}, co2={s['shipping_co2_kg_per_lb']}kg/lb, "
            f"deforestation={s['deforestation_risk']}, water={s['water_use']})"
        )
    scores = "\n".join(lines)

    prompt = (
        "You are a strict coffee sustainability auditor. Below are the computed "
        "sustainability scores for the requested farms. Do NOT change the scores or "
        "grades. Write one short sentence per farm explaining the main environmental "
        "risk or strength, then state which farm you would approve from a "
        "sustainability-only view. You only care about sustainability, not price "
        "or quality.\n\n"
        f"Scores:\n{scores}\n\nRequest: {user_message}"
    )
    note = get_llm(streaming=False).invoke(prompt).content.strip()
    logger.info("Sustainability report scores:\n%s", scores)
    return f"SUSTAINABILITY SCORES\n{scores}\n\nAUDITOR NOTE\n{note}"


@agent(name="sustainability_agent")
class SustainabilityAgent:
    async def invoke(self, user_message: str) -> str:
        result = build_sustainability_report(user_message)
        if not result.strip():
            raise RuntimeError("No valid response generated.")
        return result.strip()
