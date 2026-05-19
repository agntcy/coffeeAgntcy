# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Event sink implementations for publishing workflow events.

This module isolates event-delivery behavior from middleware flow logic.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from urllib.parse import quote

import httpx

from config.config import WORKFLOW_API_KEY, WORKFLOW_API_URL
from schema.types import Event

logger = logging.getLogger("lungo.common.event_middleware")


class EventSink(ABC):
    """Interface for event delivery backends."""

    @abstractmethod
    async def emit(self, event: Event) -> None:
        """Handle event delivery for one event."""

    async def aclose(self) -> None:
        """Release sink resources (default no-op)."""
        return None


class WorkflowAPIEventSink(EventSink):
    """Fire-and-forget sink that POSTs events to the workflow API."""

    _TIMEOUT = 5.0
    _INSTANCE_ID_PREFIX = "instance://"

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self._base_url = WORKFLOW_API_URL if base_url is None else base_url
        self._api_key = WORKFLOW_API_KEY if api_key is None else api_key

        self._client: httpx.AsyncClient | None = None
        self._pending: set[asyncio.Task] = set()

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._TIMEOUT)
        return self._client

    async def emit(self, event: Event) -> None:
        """Extract workflow/instance from event and POST in background."""
        try:
            workflow_name = next(iter(event.data.workflows))
            workflow = event.data.workflows[workflow_name]
            instance_id = next(iter(workflow.instances))
        except (StopIteration, AttributeError):
            logger.warning(
                "HttpEventSink: cannot extract workflow/instance from event, dropping."
            )
            return

        instance_uuid = instance_id
        if instance_uuid.startswith(self._INSTANCE_ID_PREFIX):
            instance_uuid = instance_uuid[len(self._INSTANCE_ID_PREFIX):]

        url = (
            f"{self._base_url}/agentic-workflows/{quote(workflow_name, safe='')}"
            f"/instances/{quote(instance_uuid, safe='')}/events/"
        )
        body = event.model_dump_json(exclude_none=True)
        task = asyncio.create_task(self._post(url, body, workflow_name, instance_uuid))
        self._pending.add(task)
        task.add_done_callback(self._pending.discard)

    async def _post(
        self, url: str, body: str, workflow_name: str, instance_uuid: str
    ) -> None:
        """Best-effort POST; errors are logged, never raised."""
        try:
            headers = {"Content-Type": "application/json"}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            resp = await self._get_client().post(
                url,
                content=body,
                headers=headers,
            )
            if resp.is_error:
                logger.warning(
                    "HttpEventSink: POST failed workflow=%s instance=%s status=%s",
                    workflow_name,
                    instance_uuid,
                    resp.status_code,
                )
                return

            logger.debug(
                "HttpEventSink: POST ok workflow=%s instance=%s status=%s",
                workflow_name,
                instance_uuid,
                resp.status_code,
            )
        except httpx.TimeoutException as exc:
            logger.warning(
                "HttpEventSink: timeout workflow=%s instance=%s (%s)",
                workflow_name,
                instance_uuid,
                exc,
            )
        except httpx.HTTPError as exc:
            logger.warning(
                "HttpEventSink: http error workflow=%s instance=%s (%s: %s)",
                workflow_name,
                instance_uuid,
                type(exc).__name__,
                exc,
            )
        except Exception as exc:
            logger.warning(
                "HttpEventSink: unexpected error workflow=%s instance=%s (%s: %s)",
                workflow_name,
                instance_uuid,
                type(exc).__name__,
                exc,
            )

    async def aclose(self) -> None:
        """Drain pending POSTs and close the underlying HTTP client."""
        if self._pending:
            await asyncio.gather(*self._pending, return_exceptions=True)
        if self._client is not None:
            await self._client.aclose()
            self._client = None
