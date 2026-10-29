# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""The ``baseline`` configuration: plain group negotiation (design D4, D6).

The moderator decides who speaks, and the agents decide what to say. Each
round the Buyer's request goes to Supplier A, B, C and then Logistics, one at
a time, and each sees the public transcript so far. The Buyer's LLM then
chooses to continue, propose a plan, withhold or escalate. A proposed plan
goes to a confirmation round with all five parties.

No ACCORD or CONCORD text, tool or message exists in this configuration. The
decision prompt below is part of the scaffold and is the same wherever the
Buyer decides, so it explains the four actions and does not hint at what to
verify.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from agents.supervisors.supply_chain.moderator import (
    MODERATOR_ID,
    Moderator,
    RoundLimitReached,
    StepFailed,
)
from agents.supervisors.supply_chain.outcome import Outcome, PlanProposal
from agents.supply_chain.common import fixtures as fx
from agents.supply_chain.common import prompts
from agents.supply_chain.common.member import render_transcript

logger = logging.getLogger("lungo.supply_chain.baseline")

# Who is addressed in a round, in this order (design D4).
ROUND_ORDER: tuple[fx.Party, ...] = (*fx.SUPPLIERS, "logistics")

NOT_CONFIRMED_REQUEST = (
    "Plan version {version} did not get everyone's confirmation. The "
    "objections are in the transcript. Please respond so that we can reach a "
    "plan that all of us can confirm."
)
CONTINUE_FALLBACK = "Please continue the negotiation."

DECISION_INSTRUCTIONS = """\
You have heard from each party in this round. Decide what to do next, as the \
buyer, and answer with exactly one action:

- continue: the negotiation is not finished. Put in "message" what you say \
to the group next.
- propose_plan: you are ready to put one complete plan to all parties for \
confirmation. Put the plan in "plan": for each supplier its tonnes, grade and \
transport option (named exactly as Logistics named it), the total transport \
cost, and what your deadline measures.
- withhold: you will not commit to any plan. Say why in "reason".
- escalate: this needs a human decision. Say why in "reason"."""


class BuyerDecision(BaseModel):
    action: Literal["continue", "propose_plan", "withhold", "escalate"]
    message: str = Field(
        default="", description="What you say to the group next (for continue)."
    )
    plan: PlanProposal | None = Field(
        default=None, description="The complete plan (for propose_plan)."
    )
    reason: str = Field(default="", description="Why (for withhold or escalate).")


class BaselineStrategy:
    name = "baseline"

    def __init__(self, llm_factory: Callable[..., Any] | None = None):
        self._llm_factory = llm_factory

    def _llm(self) -> Any:
        if self._llm_factory is not None:
            return self._llm_factory(streaming=False)
        from agents.supply_chain.common.llm import agent_llm

        return agent_llm(streaming=False)

    async def decide(self, moderator: Moderator) -> BuyerDecision:
        """The Buyer's choice after a round, from its own role and the transcript."""
        system = "\n\n".join(
            [
                prompts.buyer_prompt(fx.buyer_slice(moderator.case)),
                DECISION_INSTRUCTIONS,
            ]
        )
        transcript = render_transcript(tuple(moderator.transcript))
        structured = self._llm().with_structured_output(BuyerDecision)
        result = await structured.ainvoke(
            [
                SystemMessage(system),
                HumanMessage(f"Public transcript so far:\n{transcript}"),
            ]
        )
        decision = (
            BuyerDecision.model_validate(result) if isinstance(result, dict) else result
        )
        if decision.action == "propose_plan" and decision.plan is None:
            raise StepFailed("the Buyer proposed a plan without giving one")
        return decision

    async def run(self, moderator: Moderator) -> Outcome:
        request = fx.buyer_slice(moderator.case).opening_wording
        version = 0
        rounds = 0  # rounds that started; the moderator counts the refused one too
        rejected_replies = 0
        last_plan_rejected = False
        sender = "buyer"  # the group notice after a disruption comes from the moderator

        def signals(**extra: Any) -> dict[str, Any]:
            return {
                "rounds": rounds,
                "plans_proposed": version,
                "rejected_replies": rejected_replies,
                **extra,
            }

        while True:
            try:
                round_number = moderator.begin_round()
            except RoundLimitReached:
                reason = "party_rejected" if last_plan_rejected else "round_limit"
                return Outcome.withheld(
                    reason,
                    f"round limit of {moderator.limits.max_rounds} reached",
                    plan_version=version,
                    signals=signals(),
                )

            rounds = round_number
            for party in ROUND_ORDER:
                await moderator.step(
                    "negotiation",
                    [party],
                    request,
                    sender=sender,
                    phase=f"round_{round_number}",
                )
            sender = "buyer"

            decision = await self.decide(moderator)
            moderator.emit_status(
                "decision", round=round_number, action=decision.action
            )

            if decision.action == "withhold":
                return Outcome.withheld(
                    "buyer_decision",
                    decision.reason,
                    plan_version=version,
                    signals=signals(),
                )
            if decision.action == "escalate":
                return Outcome(
                    status="escalated",
                    reason="buyer_decision",
                    detail=decision.reason,
                    plan_version=version,
                    signals=signals(escalated=True),
                )
            if decision.action == "continue":
                request = decision.message.strip() or CONTINUE_FALLBACK
                continue

            assert decision.plan is not None
            version += 1
            confirmations = await moderator.confirm_round(decision.plan, version)
            rejections = [c for c in confirmations if c.decision == "reject"]
            rejected_replies += len(rejections)
            if not rejections:
                disruption = await moderator.inject_disruption(version)
                if disruption is not None:
                    # The plan was committed, then the world changed. The old
                    # confirmations do not carry over: negotiation resumes and
                    # the next plan is a new version (design D7).
                    request = disruption.group_notice
                    sender = MODERATOR_ID
                    continue
                return Outcome(
                    status="committed",
                    reason="buyer_decision",
                    plan=decision.plan,
                    plan_version=version,
                    signals=signals(),
                )
            last_plan_rejected = True
            request = NOT_CONFIRMED_REQUEST.format(version=version)
