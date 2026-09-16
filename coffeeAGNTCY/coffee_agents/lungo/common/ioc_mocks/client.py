# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from types import TracebackType
from typing import Self

import httpx

from common.ioc_mocks.alignment_store import (
    AlignmentDecide,
    AlignmentRound,
    AlignmentSession,
    AlignmentStart,
)
from common.ioc_mocks.intent_store import AgentIntent, IntentPublish
from common.ioc_mocks.memory_store import (
    MemoryFact,
    MemoryRecall,
    MemoryRetain,
)
from common.ioc_mocks.team_store import (
    PollOpen,
    PollResponse,
    PollResponseWrite,
    TeamPoll,
    TeamRoster,
)


class IocMockClient:
    def __init__(
        self,
        base_url: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            transport=transport,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def retain_memory(self, request: MemoryRetain) -> list[MemoryFact]:
        response = await self._client.post(
            "/mock-ioc/memory/retain",
            json=request.model_dump(mode="json"),
        )
        response.raise_for_status()
        return [MemoryFact.model_validate(item) for item in response.json()]

    async def recall_memory(self, request: MemoryRecall) -> list[MemoryFact]:
        response = await self._client.post(
            "/mock-ioc/memory/recall",
            json=request.model_dump(mode="json"),
        )
        response.raise_for_status()
        return [MemoryFact.model_validate(item) for item in response.json()]

    async def dump_memory(self, scope_id: str) -> list[MemoryFact]:
        response = await self._client.get(
            "/mock-ioc/memory",
            params={"scope_id": scope_id},
        )
        response.raise_for_status()
        return [MemoryFact.model_validate(item) for item in response.json()]

    async def publish_intent(self, request: IntentPublish) -> AgentIntent:
        response = await self._client.post(
            "/mock-ioc/intent/publish",
            json=request.model_dump(mode="json"),
        )
        response.raise_for_status()
        return AgentIntent.model_validate(response.json())

    async def query_intents(
        self,
        scope_id: str,
        actor: str | None = None,
    ) -> list[AgentIntent]:
        params = {"scope_id": scope_id}
        if actor is not None:
            params["actor"] = actor
        response = await self._client.get("/mock-ioc/intent", params=params)
        response.raise_for_status()
        return [AgentIntent.model_validate(item) for item in response.json()]

    async def intent_history(self, scope_id: str) -> list[AgentIntent]:
        response = await self._client.get(
            "/mock-ioc/intent/history",
            params={"scope_id": scope_id},
        )
        response.raise_for_status()
        return [AgentIntent.model_validate(item) for item in response.json()]

    async def open_team_poll(self, request: PollOpen) -> TeamPoll:
        response = await self._client.post(
            "/mock-ioc/team/open",
            json=request.model_dump(mode="json"),
        )
        response.raise_for_status()
        return TeamPoll.model_validate(response.json())

    async def respond_to_team_poll(
        self,
        request: PollResponseWrite,
    ) -> PollResponse:
        response = await self._client.post(
            "/mock-ioc/team/respond",
            json=request.model_dump(mode="json"),
        )
        response.raise_for_status()
        return PollResponse.model_validate(response.json())

    async def close_team_poll(self, team_id: str) -> TeamRoster:
        response = await self._client.post(
            "/mock-ioc/team/close",
            params={"team_id": team_id},
        )
        response.raise_for_status()
        return TeamRoster.model_validate(response.json())

    async def get_team_poll(self, team_id: str) -> TeamPoll:
        response = await self._client.get(
            "/mock-ioc/team",
            params={"team_id": team_id},
        )
        response.raise_for_status()
        return TeamPoll.model_validate(response.json())

    async def start_alignment(
        self,
        request: AlignmentStart,
    ) -> AlignmentRound:
        response = await self._client.post(
            "/mock-ioc/alignment/start",
            json=request.model_dump(mode="json"),
        )
        response.raise_for_status()
        return AlignmentRound.model_validate(response.json())

    async def decide_alignment(
        self,
        request: AlignmentDecide,
    ) -> AlignmentRound:
        response = await self._client.post(
            "/mock-ioc/alignment/decide",
            json=request.model_dump(mode="json"),
        )
        response.raise_for_status()
        return AlignmentRound.model_validate(response.json())

    async def get_alignment(self, session_id: str) -> AlignmentSession:
        response = await self._client.get(
            "/mock-ioc/alignment",
            params={"session_id": session_id},
        )
        response.raise_for_status()
        return AlignmentSession.model_validate(response.json())
