# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
from datetime import datetime

from pydantic import BaseModel

from common.ioc_mocks.clock import Clock, utc_now

ScalarValue = str | int | float | bool


class MemoryFactWrite(BaseModel):
    key: str
    value: ScalarValue
    actor: str


class MemoryFact(MemoryFactWrite):
    scope_id: str
    recorded_at: datetime


class MemoryRecall(BaseModel):
    scope_id: str
    keys: list[str] | None = None
    key_contains: str | None = None


class MemoryRetain(BaseModel):
    scope_id: str
    facts: list[MemoryFactWrite]


class MemoryStore:
    def __init__(self, now: Clock = utc_now) -> None:
        self._now = now
        self._facts: dict[str, dict[str, MemoryFact]] = {}
        self._lock = asyncio.Lock()

    async def retain(
        self,
        scope_id: str,
        facts: list[MemoryFactWrite],
    ) -> list[MemoryFact]:
        retained: list[MemoryFact] = []
        async with self._lock:
            scoped_facts = self._facts.setdefault(scope_id, {})
            for fact in facts:
                stored = MemoryFact(
                    scope_id=scope_id,
                    key=fact.key,
                    value=fact.value,
                    actor=fact.actor,
                    recorded_at=self._now(),
                )
                scoped_facts[fact.key] = stored
                retained.append(stored)
        return retained

    async def recall(
        self,
        scope_id: str,
        keys: list[str] | None = None,
        key_contains: str | None = None,
    ) -> list[MemoryFact]:
        async with self._lock:
            facts = list(self._facts.get(scope_id, {}).values())

        if keys is not None:
            key_set = set(keys)
            facts = [fact for fact in facts if fact.key in key_set]
        if key_contains is not None:
            facts = [fact for fact in facts if key_contains in fact.key]
        return facts

    async def dump(self, scope_id: str) -> list[MemoryFact]:
        return await self.recall(scope_id)
