# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from common.ioc_mocks.clock import Clock, utc_now
from common.ioc_mocks.errors import (
    MockStoreConflictError,
    MockStoreNotFoundError,
    MockStoreValidationError,
)


class AlignmentAction(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    COUNTER_OFFER = "counter_offer"


class AlignmentStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    AGREED = "agreed"
    BROKEN = "broken"
    TIMEOUT = "timeout"


class AlignmentStart(BaseModel):
    session_id: str
    participants: list[str]
    goal: str
    issues: dict[str, list[str]]
    max_rounds: int = 3


class AlignmentReply(BaseModel):
    participant_id: str
    action: AlignmentAction
    offer: dict[str, str] | None = None
    reason: str | None = None


class AlignmentDecide(BaseModel):
    session_id: str
    replies: list[AlignmentReply]


class AlignmentMessage(BaseModel):
    participant_id: str
    action: str
    allowed_actions: list[AlignmentAction]
    current_offer: dict[str, str]
    issues: dict[str, list[str]]


class AlignmentRound(BaseModel):
    round_index: int
    status: AlignmentStatus
    messages: list[AlignmentMessage]
    replies: list[AlignmentReply] = Field(default_factory=list)
    agreement: dict[str, str] | None = None
    recorded_at: datetime


class AlignmentSession(AlignmentStart):
    current_offer: dict[str, str]
    available_issues: dict[str, list[str]]
    rounds: list[AlignmentRound]

    @property
    def status(self) -> AlignmentStatus:
        return self.rounds[-1].status


class AlignmentNextState(BaseModel):
    offer: dict[str, str]
    available_issues: dict[str, list[str]]


class AlignmentStore:
    def __init__(self, now: Clock = utc_now) -> None:
        self._now = now
        self._sessions: dict[str, AlignmentSession] = {}
        self._lock = asyncio.Lock()

    async def start(self, request: AlignmentStart) -> AlignmentRound:
        self._validate_start(request)
        async with self._lock:
            if request.session_id in self._sessions:
                raise MockStoreConflictError("alignment session already exists")
            current_offer = {
                issue: options[0] for issue, options in request.issues.items()
            }
            first_round = self._build_round(
                participants=request.participants,
                issues=request.issues,
                current_offer=current_offer,
                round_index=1,
            )
            self._sessions[request.session_id] = AlignmentSession(
                **request.model_dump(),
                current_offer=current_offer,
                available_issues={
                    issue: list(options) for issue, options in request.issues.items()
                },
                rounds=[first_round],
            )
            return first_round.model_copy(deep=True)

    async def decide(
        self,
        session_id: str,
        replies: list[AlignmentReply],
    ) -> AlignmentRound:
        async with self._lock:
            session = self._get_session(session_id)
            if session.status is not AlignmentStatus.IN_PROGRESS:
                raise MockStoreConflictError("alignment session is terminal")
            self._validate_replies(session, replies)
            session.rounds[-1].replies = list(replies)

            if all(reply.action is AlignmentAction.ACCEPT for reply in replies):
                session.rounds[-1].status = AlignmentStatus.AGREED
                session.rounds[-1].agreement = dict(session.current_offer)
                return session.rounds[-1].model_copy(deep=True)

            next_state = self._next_state(session, replies)
            if next_state is None:
                session.rounds[-1].status = AlignmentStatus.BROKEN
                return session.rounds[-1].model_copy(deep=True)

            session.current_offer = next_state.offer
            session.available_issues = next_state.available_issues
            if len(session.rounds) >= session.max_rounds:
                session.rounds[-1].status = AlignmentStatus.TIMEOUT
                return session.rounds[-1].model_copy(deep=True)

            next_round = self._build_round(
                participants=session.participants,
                issues=session.available_issues,
                current_offer=next_state.offer,
                round_index=len(session.rounds) + 1,
            )
            session.rounds.append(next_round)
            return next_round.model_copy(deep=True)

    async def dump(self, session_id: str) -> AlignmentSession:
        async with self._lock:
            return self._get_session(session_id).model_copy(deep=True)

    def _validate_start(self, request: AlignmentStart) -> None:
        if len(request.participants) < 2:
            raise MockStoreValidationError("at least two participants are required")
        if len(request.participants) != len(set(request.participants)):
            raise MockStoreValidationError("participants must be unique")
        if request.max_rounds < 1:
            raise MockStoreValidationError("max_rounds must be positive")
        if not request.issues or any(
            not options for options in request.issues.values()
        ):
            raise MockStoreValidationError("every issue needs at least one option")

    def _validate_replies(
        self,
        session: AlignmentSession,
        replies: list[AlignmentReply],
    ) -> None:
        participant_ids = [reply.participant_id for reply in replies]
        if set(participant_ids) != set(session.participants):
            raise MockStoreValidationError("one reply per participant is required")
        if len(participant_ids) != len(set(participant_ids)):
            raise MockStoreValidationError("participants may reply only once per round")

        for reply in replies:
            if reply.action is AlignmentAction.COUNTER_OFFER:
                if reply.offer is None or set(reply.offer) != set(session.issues):
                    raise MockStoreValidationError(
                        "counter offers must include every issue"
                    )
                for issue, option in reply.offer.items():
                    if option not in session.available_issues[issue]:
                        raise MockStoreValidationError(
                            "counter offer contains an unavailable option"
                        )

    def _next_state(
        self,
        session: AlignmentSession,
        replies: list[AlignmentReply],
    ) -> AlignmentNextState | None:
        rejected = False
        for reply in replies:
            if reply.action is AlignmentAction.REJECT:
                rejected = True
                break
        if rejected:
            return self._advance_rejected_offer(session)

        counters: list[dict[str, str]] = []
        for reply in replies:
            if reply.action is AlignmentAction.COUNTER_OFFER and reply.offer is not None:
                counters.append(dict(reply.offer))
        if counters:
            first = counters[0]
            for offer in counters[1:]:
                if offer != first:
                    return None
            return AlignmentNextState(
                offer=first,
                available_issues={
                    issue: list(options)
                    for issue, options in session.available_issues.items()
                },
            )

        return self._advance_rejected_offer(session)

    def _advance_rejected_offer(
        self,
        session: AlignmentSession,
    ) -> AlignmentNextState | None:
        remaining_issues: dict[str, list[str]] = {}
        next_offer: dict[str, str] = {}
        any_choice_left = False
        for issue, options in session.available_issues.items():
            remaining: list[str] = []
            for option in options:
                if option != session.current_offer[issue]:
                    remaining.append(option)
            if remaining:
                any_choice_left = True
                remaining_issues[issue] = remaining
                next_offer[issue] = remaining[0]
                continue
            remaining_issues[issue] = [session.current_offer[issue]]
            next_offer[issue] = session.current_offer[issue]
        if not any_choice_left:
            return None
        return AlignmentNextState(
            offer=next_offer,
            available_issues=remaining_issues,
        )

    def _build_round(
        self,
        participants: list[str],
        issues: dict[str, list[str]],
        current_offer: dict[str, str],
        round_index: int,
    ) -> AlignmentRound:
        proposer_index = (round_index - 1) % len(participants)
        messages = [
            AlignmentMessage(
                participant_id=participant,
                action="propose" if index == proposer_index else "respond",
                allowed_actions=list(AlignmentAction),
                current_offer=dict(current_offer),
                issues={issue: list(options) for issue, options in issues.items()},
            )
            for index, participant in enumerate(participants)
        ]
        return AlignmentRound(
            round_index=round_index,
            status=AlignmentStatus.IN_PROGRESS,
            messages=messages,
            recorded_at=self._now(),
        )

    def _get_session(self, session_id: str) -> AlignmentSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise MockStoreNotFoundError("alignment session not found")
        return session
