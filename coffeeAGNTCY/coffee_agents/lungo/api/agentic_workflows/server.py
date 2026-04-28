# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Standalone HTTP service for the Agentic Workflows API."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from api.agentic_workflows.router import (
    WORKFLOW_INSTANCE_STORE_ATTR,
    create_agentic_workflows_router,
)
from api.agentic_workflows.workflows import set_starting_workflows
from common.cors import get_cors_allowed_origins
from common.workflow_instance_store import WorkflowInstanceStateStore

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


logger = logging.getLogger("lungo.agentic_workflows.server")


@asynccontextmanager
async def _close_workflow_instance_store_on_shutdown(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI ``lifespan`` hook: shutdown-only cleanup for ``app.state`` resources.

    Starlette/FastAPI use the parameter name ``lifespan`` for this async context
    manager (startup before ``yield``, shutdown after). Today we only need
    shutdown to close the workflow-instance store; startup is a no-op.
    """
    yield
    store = getattr(app.state, WORKFLOW_INSTANCE_STORE_ATTR, None)
    if store is not None:
        store.close()


def create_agentic_workflows_app() -> FastAPI:
    """FastAPI app exposing only the agentic-workflows router plus ``/health``."""
    cors_origins = get_cors_allowed_origins()
    logger.info("CORS allow_origins: %s", cors_origins)

    app = FastAPI(
        title="Agentic Workflows API",
        version="1.0.0",
        description="Catalog, workflow instances, internal events, SSE.",
        lifespan=_close_workflow_instance_store_on_shutdown,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    setattr(app.state, WORKFLOW_INSTANCE_STORE_ATTR, WorkflowInstanceStateStore())
    app.include_router(create_agentic_workflows_router())
    return app


set_starting_workflows()
app = create_agentic_workflows_app()


def main() -> None:
    port = int(os.environ.get("PORT", "9105"))
    logger.info("Starting Agentic Workflows API on 0.0.0.0:%s", port)
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
