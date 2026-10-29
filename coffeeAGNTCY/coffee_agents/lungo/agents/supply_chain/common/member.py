# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""One LLM-backed participant (supplier, logistics, or the Buyer's persona).

Every party is the same class with a different role prompt, so agents differ
only by their fixture slice. The class implements the D3 addressing gate and
the D6 confirmation reply. ACCORD and CONCORD requests are refused: the L9
protocol is not implemented yet.
"""

from __future__ import annotations

import json
import logging
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, get_args

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from pydantic import BaseModel

from agents.supply_chain.common import fixtures as fx
from agents.supply_chain.common import prompts
from agents.supply_chain.common.envelope import Envelope, Kind, noop, reply
from agents.supply_chain.common.skills import l9_enabled

logger = logging.getLogger("lungo.supply_chain.member")

MAX_RUNS_REMEMBERED = 32
READY_TIME_CHANGE = "ready_time_change"

# Request kind -> the kind a member answers it with. The moderator uses the
# same table to check every reply.
REPLY_KIND: dict[str, Kind] = {
    "negotiation": "negotiation",
    "event": "negotiation",
    "confirm_request": "confirm_reply",
    "accord_request": "accord_reply",
    "concord_request": "concord_reply",
}

_NEGOTIATION_INSTRUCTIONS = (
    "Write your next message to the group, as plain text, speaking for your "
    "organization. Do not use JSON."
)
_CONFIRM_INSTRUCTIONS = (
    "You are asked whether your organization confirms the plan version "
    "described in the request. Decide using only your own organization's "
    "facts and requirements, then reply confirm or reject with a reason."
)
LlmFactory = Callable[..., Any]

L9_KINDS = ("accord_request", "concord_request")


class L9Disabled(RuntimeError):
    """An ACCORD or CONCORD request reached an agent that cannot serve it.

    Either the L9 switch is off, or the switch is on but the protocol is not
    implemented yet. Raised, not answered with protocol content, so the sender
    sees a failed step (a ``protocol_error`` run, graded ``INVALID``) and a
    deployment where only some agents have L9 on cannot pass for a working run.
    """


class ConfirmDecision(BaseModel):
    decision: Literal["confirm", "reject"]
    reason: str


@dataclass
class _RunState:
    disrupted: bool = False


def render_transcript(transcript: tuple[dict[str, object], ...]) -> str:
    lines = []
    for entry in transcript:
        to = entry.get("to") or []
        recipients = ", ".join(to) if isinstance(to, (list, tuple)) else str(to)
        lines.append(
            f"[{entry.get('seq', '?')}] {entry.get('from', '?')} -> {recipients}: "
            f"{entry.get('body', '')}"
        )
    return "\n".join(lines)


class MemberAgent:
    def __init__(
        self,
        party: fx.Party,
        llm_factory: LlmFactory | None = None,
        *,
        l9: bool | None = None,
    ):
        if party not in get_args(fx.Party):
            raise ValueError(f"unknown party {party!r}")
        self.party = party
        self._llm_factory = llm_factory
        # Read once, at start-up, so a bad value stops the agent right away.
        self.l9_enabled = l9_enabled() if l9 is None else l9
        logger.info("%s: L9 (ACCORD, CONCORD) enabled: %s", party, self.l9_enabled)
        self._runs: OrderedDict[str, _RunState] = OrderedDict()

    def _llm(self) -> Any:
        if self._llm_factory is not None:
            return self._llm_factory(streaming=False)
        from agents.supply_chain.common.llm import agent_llm

        return agent_llm(streaming=False)

    def _state(self, run_id: str) -> _RunState:
        state = self._runs.get(run_id)
        if state is None:
            state = self._runs[run_id] = _RunState()
            while len(self._runs) > MAX_RUNS_REMEMBERED:
                self._runs.popitem(last=False)
        else:
            self._runs.move_to_end(run_id)
        return state

    def role_prompt(self, case: str, disrupted: bool = False) -> str:
        if case not in fx.CASES:
            raise ValueError(f"unknown case {case!r}")
        if self.party == "buyer":
            return prompts.buyer_prompt(fx.buyer_slice(case))
        if self.party == "logistics":
            return prompts.logistics_prompt(fx.logistics_slice(case))
        return prompts.supplier_prompt(fx.supplier_slice(self.party, case, disrupted))

    def _system_prompt(self, request: Envelope, state: _RunState) -> str:
        parts = [self.role_prompt(request.case, state.disrupted)]
        if request.kind == "confirm_request":
            parts.append(_CONFIRM_INSTRUCTIONS)
        else:
            parts.append(_NEGOTIATION_INSTRUCTIONS)
        return "\n\n".join(parts)

    def _messages(self, request: Envelope, state: _RunState) -> list[BaseMessage]:
        messages: list[BaseMessage] = [
            SystemMessage(self._system_prompt(request, state))
        ]
        text = request.body
        if request.transcript:
            text = (
                "Public transcript so far:\n"
                f"{render_transcript(request.transcript)}\n\nRequest:\n{request.body}"
            )
        messages.append(HumanMessage(text))
        return messages

    async def handle(self, request: Envelope) -> Envelope:
        if request.kind in ("noop", "control") or not request.addressed_to(self.party):
            return noop(request, self.party)
        if request.kind in L9_KINDS:
            # Before any prompt is built: no model is called.
            reason = (
                "SUPPLY_CHAIN_L9_ENABLED is off"
                if not self.l9_enabled
                else "the L9 protocol is not implemented yet"
            )
            raise L9Disabled(f"{request.kind} refused: {reason} for {self.party}")

        state = self._state(request.run_id)
        if request.kind == "event" and request.phase == READY_TIME_CHANGE:
            state.disrupted = True

        messages = self._messages(request, state)
        kind = REPLY_KIND[request.kind]
        if request.kind == "confirm_request":
            body = await self._confirm(messages)
        else:
            body = _text(await self._llm().ainvoke(messages))

        return reply(request, self.party, kind, body)

    async def _confirm(self, messages: list[BaseMessage]) -> str:
        structured = self._llm().with_structured_output(ConfirmDecision)
        decision = await structured.ainvoke(messages)
        if isinstance(decision, dict):
            decision = ConfirmDecision.model_validate(decision)
        return json.dumps({"decision": decision.decision, "reason": decision.reason})


def _text(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content)
