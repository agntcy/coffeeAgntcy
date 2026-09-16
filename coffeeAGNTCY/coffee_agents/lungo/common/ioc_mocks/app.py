# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from common.cors import get_cors_allowed_origins
from common.ioc_mocks.alignment_store import (
    AlignmentDecide,
    AlignmentRound,
    AlignmentSession,
    AlignmentStart,
    AlignmentStore,
)
from common.ioc_mocks.errors import (
    MockStoreConflictError,
    MockStoreNotFoundError,
    MockStoreValidationError,
)
from common.ioc_mocks.intent_store import AgentIntent, IntentPublish, IntentStore
from common.ioc_mocks.memory_store import (
    MemoryFact,
    MemoryRecall,
    MemoryRetain,
    MemoryStore,
)
from common.ioc_mocks.team_store import (
    PollOpen,
    PollResponse,
    PollResponseWrite,
    TeamPoll,
    TeamRoster,
    TeamStore,
)


async def handle_not_found(
    _request: Request,
    exc: MockStoreNotFoundError,
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def handle_conflict(
    _request: Request,
    exc: MockStoreConflictError,
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


async def handle_validation(
    _request: Request,
    exc: MockStoreValidationError,
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


class IocMockController:
    def __init__(
        self,
        memory_store: MemoryStore,
        intent_store: IntentStore,
        team_store: TeamStore,
        alignment_store: AlignmentStore,
    ) -> None:
        self.memory_store = memory_store
        self.intent_store = intent_store
        self.team_store = team_store
        self.alignment_store = alignment_store

    async def health(self) -> dict[str, str]:
        return {"status": "ok"}

    async def retain_memory(self, request: MemoryRetain) -> list[MemoryFact]:
        return await self.memory_store.retain(request.scope_id, request.facts)

    async def recall_memory(self, request: MemoryRecall) -> list[MemoryFact]:
        return await self.memory_store.recall(
            request.scope_id,
            request.keys,
            request.key_contains,
        )

    async def dump_memory(
        self,
        scope_id: str = Query(min_length=1),
    ) -> list[MemoryFact]:
        return await self.memory_store.dump(scope_id)

    async def publish_intent(self, request: IntentPublish) -> AgentIntent:
        return await self.intent_store.publish(
            request.scope_id,
            request.actor,
            request.goal,
            request.details,
        )

    async def query_intents(
        self,
        scope_id: str = Query(min_length=1),
        actor: str | None = None,
    ) -> list[AgentIntent]:
        return await self.intent_store.query(scope_id, actor)

    async def intent_history(
        self,
        scope_id: str = Query(min_length=1),
    ) -> list[AgentIntent]:
        return await self.intent_store.dump(scope_id)

    async def open_team_poll(self, request: PollOpen) -> TeamPoll:
        return await self.team_store.open_poll(request)

    async def respond_to_team_poll(
        self,
        request: PollResponseWrite,
    ) -> PollResponse:
        return await self.team_store.respond(request)

    async def close_team_poll(self, team_id: str = Query(min_length=1)) -> TeamRoster:
        return await self.team_store.close_poll(team_id)

    async def get_team_poll(
        self,
        team_id: str = Query(min_length=1),
    ) -> TeamPoll:
        return await self.team_store.dump(team_id)

    async def start_alignment(self, request: AlignmentStart) -> AlignmentRound:
        return await self.alignment_store.start(request)

    async def decide_alignment(self, request: AlignmentDecide) -> AlignmentRound:
        return await self.alignment_store.decide(
            request.session_id,
            request.replies,
        )

    async def get_alignment(
        self,
        session_id: str = Query(min_length=1),
    ) -> AlignmentSession:
        return await self.alignment_store.dump(session_id)


def add_routes(app: FastAPI, controller: IocMockController) -> None:
    app.add_api_route("/v1/health", controller.health, methods=["GET"])
    app.add_api_route(
        "/mock-ioc/memory/retain",
        controller.retain_memory,
        methods=["POST"],
    )
    app.add_api_route(
        "/mock-ioc/memory/recall",
        controller.recall_memory,
        methods=["POST"],
    )
    app.add_api_route("/mock-ioc/memory", controller.dump_memory, methods=["GET"])
    app.add_api_route(
        "/mock-ioc/intent/publish",
        controller.publish_intent,
        methods=["POST"],
    )
    app.add_api_route("/mock-ioc/intent", controller.query_intents, methods=["GET"])
    app.add_api_route(
        "/mock-ioc/intent/history",
        controller.intent_history,
        methods=["GET"],
    )
    app.add_api_route(
        "/mock-ioc/team/open",
        controller.open_team_poll,
        methods=["POST"],
    )
    app.add_api_route(
        "/mock-ioc/team/respond",
        controller.respond_to_team_poll,
        methods=["POST"],
    )
    app.add_api_route(
        "/mock-ioc/team/close",
        controller.close_team_poll,
        methods=["POST"],
    )
    app.add_api_route("/mock-ioc/team", controller.get_team_poll, methods=["GET"])
    app.add_api_route(
        "/mock-ioc/alignment/start",
        controller.start_alignment,
        methods=["POST"],
    )
    app.add_api_route(
        "/mock-ioc/alignment/decide",
        controller.decide_alignment,
        methods=["POST"],
    )
    app.add_api_route(
        "/mock-ioc/alignment",
        controller.get_alignment,
        methods=["GET"],
    )


def create_app(
    memory_store: MemoryStore | None = None,
    intent_store: IntentStore | None = None,
    team_store: TeamStore | None = None,
    alignment_store: AlignmentStore | None = None,
) -> FastAPI:
    app = FastAPI(title="Lungo IoC mock store")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(MockStoreNotFoundError, handle_not_found)
    app.add_exception_handler(MockStoreConflictError, handle_conflict)
    app.add_exception_handler(MockStoreValidationError, handle_validation)
    controller = IocMockController(
        memory_store or MemoryStore(),
        intent_store or IntentStore(),
        team_store or TeamStore(),
        alignment_store or AlignmentStore(),
    )
    add_routes(app, controller)
    return app


app = create_app()
