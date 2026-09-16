# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
from datetime import datetime

from pydantic import BaseModel, Field

from common.ioc_mocks.clock import Clock, utc_now
from common.ioc_mocks.errors import (
    MockStoreConflictError,
    MockStoreNotFoundError,
    MockStoreValidationError,
)
from common.ioc_mocks.memory_store import ScalarValue


class PollOpen(BaseModel):
    team_id: str
    roles: list[str]
    constraints: dict[str, ScalarValue] = Field(default_factory=dict)
    deadline: datetime | None = None


class PollResponseWrite(BaseModel):
    team_id: str
    actor: str
    role: str
    accepted: bool
    availability: str | None = None
    capability: str | None = None
    willingness: str | None = None


class PollResponse(PollResponseWrite):
    recorded_at: datetime


class TeamRoster(BaseModel):
    team_id: str
    bindings: dict[str, str]
    declined: list[str]
    unfilled: list[str]
    closed_at: datetime
    partial: bool


class TeamPoll(PollOpen):
    responses: list[PollResponse] = Field(default_factory=list)
    roster: TeamRoster | None = None


class TeamStore:
    def __init__(self, now: Clock = utc_now) -> None:
        self._now = now
        self._polls: dict[str, TeamPoll] = {}
        self._lock = asyncio.Lock()

    async def open_poll(self, request: PollOpen) -> TeamPoll:
        if not request.roles or len(request.roles) != len(set(request.roles)):
            raise MockStoreValidationError("roles must be non-empty and unique")
        async with self._lock:
            if request.team_id in self._polls:
                raise MockStoreConflictError("team poll already exists")
            poll = TeamPoll(**request.model_dump())
            self._polls[request.team_id] = poll
            return poll.model_copy(deep=True)

    async def respond(self, request: PollResponseWrite) -> PollResponse:
        async with self._lock:
            poll = self._get_poll(request.team_id)
            if poll.roster is not None:
                raise MockStoreConflictError("team poll is closed")
            if poll.deadline is not None and self._now() > poll.deadline:
                raise MockStoreConflictError("team poll deadline has passed")
            if request.role not in poll.roles:
                raise MockStoreValidationError("role is not part of the poll")
            if (
                any(
                    response.accepted and response.role == request.role
                    for response in poll.responses
                )
                and request.accepted
            ):
                raise MockStoreConflictError("role is already accepted")

            response = PollResponse(
                **request.model_dump(),
                recorded_at=self._now(),
            )
            poll.responses.append(response)
            return response.model_copy(deep=True)

    async def close_poll(self, team_id: str) -> TeamRoster:
        async with self._lock:
            poll = self._get_poll(team_id)
            if poll.roster is not None:
                return poll.roster.model_copy(deep=True)

            bindings = {
                response.role: response.actor
                for response in poll.responses
                if response.accepted
            }
            unfilled = [role for role in poll.roles if role not in bindings]
            declined: list[str] = []
            for response in poll.responses:
                if not response.accepted and response.actor not in declined:
                    declined.append(response.actor)
            roster = TeamRoster(
                team_id=team_id,
                bindings=bindings,
                declined=declined,
                unfilled=unfilled,
                closed_at=self._now(),
                partial=bool(unfilled),
            )
            poll.roster = roster
            return roster.model_copy(deep=True)

    async def roster(self, team_id: str) -> TeamRoster | None:
        async with self._lock:
            poll = self._get_poll(team_id)
            if poll.roster is None:
                return None
            return poll.roster.model_copy(deep=True)

    async def dump(self, team_id: str) -> TeamPoll:
        async with self._lock:
            return self._get_poll(team_id).model_copy(deep=True)

    def _get_poll(self, team_id: str) -> TeamPoll:
        poll = self._polls.get(team_id)
        if poll is None:
            raise MockStoreNotFoundError("team poll not found")
        return poll
