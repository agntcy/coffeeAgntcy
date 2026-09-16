# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
from datetime import datetime

from pydantic import BaseModel, Field

from common.ioc_mocks.clock import Clock, utc_now
from common.ioc_mocks.memory_store import ScalarValue


class IntentPublish(BaseModel):
    scope_id: str
    actor: str
    goal: str
    details: dict[str, ScalarValue] = Field(default_factory=dict)


class AgentIntent(IntentPublish):
    version: int
    published_at: datetime


class IntentStore:
    def __init__(self, now: Clock = utc_now) -> None:
        self._now = now
        self._history: dict[str, dict[str, list[AgentIntent]]] = {}
        self._lock = asyncio.Lock()

    async def publish(
        self,
        scope_id: str,
        actor: str,
        goal: str,
        details: dict[str, ScalarValue] | None = None,
    ) -> AgentIntent:
        async with self._lock:
            scoped_history = self._history.setdefault(scope_id, {})
            actor_history = scoped_history.setdefault(actor, [])
            intent = AgentIntent(
                scope_id=scope_id,
                actor=actor,
                version=len(actor_history) + 1,
                goal=goal,
                details=details or {},
                published_at=self._now(),
            )
            actor_history.append(intent)
            return intent

    async def query(
        self,
        scope_id: str,
        actor: str | None = None,
    ) -> list[AgentIntent]:
        async with self._lock:
            scoped_history = self._history.get(scope_id, {})
            if actor is not None:
                actor_history = scoped_history.get(actor, [])
                return list(actor_history[-1:])
            return [history[-1] for history in scoped_history.values() if history]

    async def dump(self, scope_id: str) -> list[AgentIntent]:
        async with self._lock:
            scoped_history = self._history.get(scope_id, {})
            return [
                intent
                for actor_history in scoped_history.values()
                for intent in actor_history
            ]
