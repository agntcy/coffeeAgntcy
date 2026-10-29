# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""The run moderator (design D3, D4, D8).

The Buyer process holds the run loop. A strategy decides who is addressed and
what is asked; the moderator delivers each step, checks that every addressee
answered exactly once, numbers every message, keeps the public transcript,
writes the run files and, after the strategy ends, builds the record and runs
the checker. The checker's result goes to the stream and the files only.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from agents.supervisors.supply_chain.limits import SCAFFOLD_VERSION, Limits
from agents.supply_chain.common.prompts import PROMPT_VERSION
from agents.supervisors.supply_chain.outcome import Outcome, PlanProposal
from agents.supervisors.supply_chain.record_builder import RunFacts, build_record
from agents.supervisors.supply_chain.transport import GroupTransport, TransportError
from agents.supply_chain.common import fixtures as fx
from agents.supply_chain.common.checker import check, mark_silent
from agents.supply_chain.common.envelope import RUN_END, Envelope, Kind
from agents.supply_chain.common.member import READY_TIME_CHANGE, REPLY_KIND, MemberAgent
from agents.supply_chain.common.record import Confirmation

logger = logging.getLogger("lungo.supply_chain.moderator")

# Kinds that members may see in the public transcript. Protocol kinds
# (ACCORD, CONCORD) stay out: ACCORD requires memory independence (D5).
PUBLIC_KINDS: frozenset[str] = frozenset(
    {"negotiation", "event", "confirm_request", "confirm_reply"}
)

BUYER: fx.Party = "buyer"
MODERATOR_ID = "moderator"


class StepFailed(Exception):
    """A step broke the one-reply-per-addressee rule or could not be delivered."""


class RoundLimitReached(Exception):
    """The strategy started more rounds than ``Limits.max_rounds``."""


class Strategy(Protocol):
    name: str

    async def run(self, moderator: Moderator) -> Outcome: ...


@dataclass
class RunResult:
    outcome: Outcome
    record: dict[str, Any]
    verdict: dict[str, Any]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Moderator:
    def __init__(
        self,
        *,
        run_id: str,
        case: fx.CaseId,
        configuration: str,
        transport: GroupTransport,
        buyer: MemberAgent,
        limits: Limits,
        run_dir: Path,
        emit: Callable[[dict[str, Any]], None] = lambda event: None,
        meta: dict[str, Any] | None = None,
    ):
        self.run_id = run_id
        self.case = case
        self.configuration = configuration
        self.limits = limits
        self.run_dir = run_dir
        self._transport = transport
        self._buyer = buyer
        self._emit = emit
        self._meta = meta or {}
        self._seq = 0
        self.round = 0
        self.log: list[Envelope] = []
        self.transcript: list[dict[str, Any]] = []
        self.confirmations: list[Confirmation] = []
        self.disruption_injected = False
        self.superseded_versions: list[int] = []
        self._round_limit = limits.max_rounds

    # -- files and events ---------------------------------------------------

    @property
    def l9_dir(self) -> Path:
        """Where the vendored initiator scripts keep their state files."""
        path = self.run_dir / "l9"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _write_json(self, name: str, data: Any) -> None:
        (self.run_dir / name).write_text(
            json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )

    def _append_message(self, envelope: Envelope) -> None:
        with (self.run_dir / "messages.jsonl").open("a", encoding="utf-8") as f:
            f.write(envelope.encode() + "\n")

    def emit_status(self, state: str, **fields: Any) -> None:
        self._emit({"type": "status", "state": state, **fields})

    @staticmethod
    def _entry(envelope: Envelope) -> dict[str, Any]:
        return {
            "seq": envelope.seq,
            "from": envelope.sender,
            "to": list(envelope.to),
            "kind": envelope.kind,
            "phase": envelope.phase,
            "plan_version": envelope.plan_version,
            "reply_to": envelope.reply_to,
            "body": envelope.body,
        }

    def _record_message(self, envelope: Envelope, *, public: bool = True) -> None:
        self.log.append(envelope)
        self._append_message(envelope)
        entry = self._entry(envelope)
        if public and envelope.kind in PUBLIC_KINDS:
            self.transcript.append(entry)
        self._emit({"type": "message", **entry})

    def _take_seq(self) -> int:
        self._seq += 1
        return self._seq

    # -- rounds and steps ---------------------------------------------------

    def begin_round(self) -> int:
        self.round += 1
        if self.round > self._round_limit:
            raise RoundLimitReached
        self.emit_status("round", round=self.round)
        return self.round

    async def step(
        self,
        kind: Kind,
        to: Sequence[fx.Party],
        body: str,
        *,
        sender: str = MODERATOR_ID,
        phase: str = "",
        plan_version: int = 0,
        private: bool = False,
    ) -> dict[fx.Party, Envelope]:
        """Deliver one request and return exactly one reply per addressee.

        A ``private`` request is logged and streamed but kept out of the public
        transcript the other parties see; the replies are always public.
        """
        if kind not in REPLY_KIND:
            raise ValueError(f"{kind!r} is not a request kind")
        recipients = tuple(dict.fromkeys(to))
        if not recipients:
            raise ValueError("a step needs at least one addressee")
        if sender in recipients:
            raise ValueError(f"{sender!r} cannot address itself")

        request = Envelope(
            run_id=self.run_id,
            seq=self._take_seq(),
            sender=sender,
            to=recipients,
            kind=kind,
            phase=phase,
            plan_version=plan_version,
            case=self.case,
            configuration=self.configuration,
            body=body,
            transcript=tuple(self.transcript) if kind in PUBLIC_KINDS else (),
        )
        self._record_message(request, public=not private)

        remote = [p for p in recipients if p != BUYER]
        # The Buyer's persona is a separate participant that runs in this
        # process, so it is called directly and not over SLIM.
        results = await asyncio.gather(
            self._deliver(request, remote) if remote else _nothing(),
            self._buyer.handle(request) if BUYER in recipients else _nothing(),
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, BaseException):
                if isinstance(result, asyncio.CancelledError):
                    raise result
                if isinstance(result, StepFailed):
                    raise result
                raise StepFailed(f"{type(result).__name__}: {result}") from result
        remote_replies, buyer_reply = results
        replies: list[Envelope] = list(remote_replies or [])
        if buyer_reply is not None:
            replies.append(buyer_reply)

        by_party = self._validate(request, replies)
        ordered = {party: by_party[party] for party in recipients}
        numbered: dict[fx.Party, Envelope] = {}
        for party, reply in ordered.items():
            numbered_reply = reply.model_copy(update={"seq": self._take_seq()})
            self._record_message(numbered_reply)
            numbered[party] = numbered_reply
        return numbered

    async def confirm_round(
        self, plan: PlanProposal, plan_version: int
    ) -> list[Confirmation]:
        """Ask all five parties to confirm one plan version (design D6).

        Each party answers from its own data. The confirmations are kept on
        the moderator and returned. A reply that is not a confirm or a reject
        fails the step, because a guess here would decide the verdict.
        """
        replies = await self.step(
            "confirm_request",
            fx.PARTIES,
            plan.render(plan_version),
            phase="confirm",
            plan_version=plan_version,
        )
        confirmations: list[Confirmation] = []
        for party, reply in replies.items():
            decision, reason = _read_confirmation(party, reply.body)
            confirmations.append(
                Confirmation(
                    party=party,
                    plan_version=plan_version,
                    decision=decision,
                    seq=reply.seq,
                    reason=reason,
                )
            )
        self.confirmations.extend(confirmations)
        return confirmations

    async def inject_disruption(self, committed_version: int) -> fx.Disruption | None:
        """Change the world after a first commitment (design D7).

        Only the affected supplier is told, privately, and it reports the
        change in its own words, publicly. The committed version is marked
        superseded, so its confirmations never count for a later version. The
        resumed negotiation gets a fresh round budget. Returns the disruption
        so the strategy can put the group notice to the parties, or ``None``
        when the case has no disruption or it was already injected.
        """
        disruption = fx.disruption_for(self.case)
        if disruption is None or self.disruption_injected:
            return None
        self.disruption_injected = True
        self.superseded_versions.append(committed_version)
        self._round_limit = self.round + self.limits.max_rounds
        self.emit_status("disruption", plan_version=committed_version)
        await self.step(
            "event",
            [disruption.supplier],
            disruption.supplier_notice,
            phase=READY_TIME_CHANGE,
            plan_version=committed_version,
            private=True,
        )
        return disruption

    async def _deliver(
        self, request: Envelope, remote: Sequence[fx.Party]
    ) -> list[Envelope]:
        try:
            return await self._transport.broadcast(
                request, remote, timeout=self.limits.step_timeout
            )
        except TransportError as e:
            raise StepFailed(str(e)) from e

    def _validate(
        self, request: Envelope, replies: Sequence[Envelope]
    ) -> dict[fx.Party, Envelope]:
        expected_kind = REPLY_KIND[request.kind]
        by_party: dict[fx.Party, Envelope] = {}
        for reply in replies:
            if reply.kind == "noop":
                raise StepFailed(f"{reply.sender} answered a step as if not addressed")
            if reply.sender not in request.to:
                raise StepFailed(f"reply from unaddressed party {reply.sender!r}")
            if reply.sender in by_party:
                raise StepFailed(f"{reply.sender} replied more than once")
            if reply.run_id != self.run_id or reply.reply_to != request.seq:
                raise StepFailed(f"reply from {reply.sender} answers another step")
            if reply.kind != expected_kind:
                raise StepFailed(
                    f"{reply.sender} replied with kind {reply.kind!r}, "
                    f"expected {expected_kind!r}"
                )
            by_party[reply.sender] = reply  # type: ignore[index]
        missing = [p for p in request.to if p not in by_party]
        if missing:
            raise StepFailed(f"no reply from {', '.join(missing)}")
        return by_party

    # -- the run ------------------------------------------------------------

    def facts(self) -> RunFacts:
        return RunFacts(
            run_id=self.run_id,
            case=self.case,
            configuration=self.configuration,
            confirmations=list(self.confirmations),
            disruption_injected=self.disruption_injected,
            superseded_versions=list(self.superseded_versions),
            log=list(self.log),
        )

    async def run(self, strategy: Strategy) -> RunResult:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(
            "meta.json",
            {
                "run_id": self.run_id,
                "case": self.case,
                "configuration": self.configuration,
                "strategy": strategy.name,
                "scaffold_version": SCAFFOLD_VERSION,
                "prompt_version": PROMPT_VERSION,
                "started_at": _now(),
                "limits": {
                    "max_rounds": self.limits.max_rounds,
                    "run_timeout": self.limits.run_timeout,
                    "step_timeout": self.limits.step_timeout,
                    "concord_threshold": self.limits.concord_threshold,
                    "concord_budget": self.limits.concord_budget,
                },
                **self._meta,
            },
        )
        self.emit_status("started", run_id=self.run_id)
        try:
            outcome = await self._run_strategy(strategy)
        except asyncio.CancelledError:
            self._write_json(
                "outcome.json",
                {"status": "cancelled", "ended_at": _now()},
            )
            raise

        # RUN_END ends the agent conversation. It is logged and streamed but
        # not delivered to any agent; nothing agent-facing follows it.
        end = Envelope(
            run_id=self.run_id,
            seq=self._take_seq(),
            sender=MODERATOR_ID,
            to=fx.PARTIES,
            kind="control",
            body=RUN_END,
            case=self.case,
            configuration=self.configuration,
        )
        self._record_message(end)

        record = build_record(outcome, self.facts())
        verdict = mark_silent(check(record, self.case), record, outcome.signals)
        record_data = record.model_dump(mode="json")
        verdict_data = verdict.model_dump(mode="json")
        self._write_json(
            "outcome.json",
            {
                "status": outcome.status,
                "reason": outcome.reason,
                "detail": outcome.detail,
                "plan_version": outcome.plan_version,
                "signals": outcome.signals,
                "ended_at": _now(),
            },
        )
        self._write_json("record.json", record_data)
        self._write_json("verdict.json", verdict_data)
        self._emit({"type": "record", "record": record_data})
        self._emit({"type": "verdict", "verdict": verdict_data})
        return RunResult(outcome=outcome, record=record_data, verdict=verdict_data)

    async def _run_strategy(self, strategy: Strategy) -> Outcome:
        deadline = asyncio.timeout(self.limits.run_timeout)
        try:
            async with deadline:
                return await strategy.run(self)
        except RoundLimitReached:
            return Outcome.withheld("round_limit", "round limit reached")
        except TimeoutError as e:
            # Only our own deadline counts as the run timeout; any other
            # TimeoutError is a failure inside the strategy.
            if not deadline.expired():
                logger.exception("Run %s failed", self.run_id)
                return Outcome.withheld("protocol_error", f"TimeoutError: {e}")
            return Outcome.withheld(
                "timeout", f"run timeout of {self.limits.run_timeout:g} s reached"
            )
        except StepFailed as e:
            logger.warning("Run %s stopped by a failed step: %s", self.run_id, e)
            return Outcome.withheld("protocol_error", str(e))
        except Exception as e:
            logger.exception("Run %s failed", self.run_id)
            return Outcome.withheld("protocol_error", f"{type(e).__name__}: {e}")


def _read_confirmation(party: str, body: str) -> tuple[str, str]:
    try:
        data = json.loads(body)
        decision = data["decision"]
        reason = str(data.get("reason", ""))
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        raise StepFailed(f"{party} sent an unreadable confirmation: {e}") from e
    if decision not in ("confirm", "reject"):
        raise StepFailed(f"{party} answered {decision!r}, not confirm or reject")
    return decision, reason


async def _nothing() -> None:
    return None
