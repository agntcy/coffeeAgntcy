# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Runs one Supply Chain Commitment run and streams its events (design D9).

This is the Buyer's counterpart of the logistics graph: it selects the case
and configuration, builds the moderator, runs the strategy, and yields every
event (``status``, ``message``, ``record``, ``verdict``) as a dict.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from collections.abc import AsyncIterator, Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.supervisors.supply_chain.limits import (
    Limits,
    run_root_from_env,
)
from agents.supervisors.supply_chain.moderator import Moderator
from agents.supervisors.supply_chain.selection import (
    L9_CONFIGURATIONS,
    L9_DISABLED_MESSAGE,
    resolve_selection,
)
from agents.supervisors.supply_chain.strategies import (
    ConfigurationNotImplemented,
    get_strategy,
)
from agents.supervisors.supply_chain.transport import GroupTransport
from agents.supply_chain.common.member import MemberAgent
from agents.supply_chain.common.skills import l9_enabled
from common.workflow_context_prop import (
    attach_workflow_context,
    detach_workflow_context,
    read_workflow_context,
)

logger = logging.getLogger("lungo.supply_chain.runner")

# Must match starting_workflows.json. Drift is guarded by the corresponding
# supply chain unit test.
_WORKFLOW_NAME = "Supply Chain Commitment"


def new_run_id() -> str:
    return f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:6]}"


class SupplyChainRunner:
    def __init__(
        self,
        transport: GroupTransport,
        *,
        buyer: MemberAgent | None = None,
        limits: Limits | None = None,
        run_root: Path | None = None,
        llm_factory: Callable[..., Any] | None = None,
        model: str = "",
        l9: bool | None = None,
    ):
        self._transport = transport
        self._llm_factory = llm_factory
        # Whether ACCORD and CONCORD may run at all (design D12); read at
        # start-up so a bad value stops the Buyer right away.
        self.l9_enabled = l9_enabled() if l9 is None else l9
        self._buyer = buyer or MemberAgent("buyer", llm_factory, l9=self.l9_enabled)
        self._limits = limits or Limits.from_env()
        self._run_root = run_root or run_root_from_env()
        self._model = model

    async def stream(
        self,
        prompt: str,
        *,
        case: str | None = None,
        configuration: str | None = None,
        workflow_instance_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        # Manual attach/detach: an async generator may be closed from another
        # task, which breaks a ``with`` scope (same reason as the logistics graph).
        existing = read_workflow_context()
        token = attach_workflow_context(
            workflow_name=existing.workflow_name or _WORKFLOW_NAME,
            workflow_instance_id=(
                existing.instance_id
                or workflow_instance_id
                or f"instance://{uuid.uuid4()}"
            ),
        )
        try:
            selection = await resolve_selection(
                prompt, case, configuration, llm_factory=self._llm_factory
            )
            yield {
                "type": "status",
                "state": "selected",
                "case": selection.case,
                "configuration": selection.configuration,
                "sources": selection.sources,
                "message": selection.describe(),
            }
            if not self.l9_enabled and selection.configuration in L9_CONFIGURATIONS:
                # No agent is contacted and no run directory is created.
                yield {
                    "type": "status",
                    "state": "l9_disabled",
                    "message": L9_DISABLED_MESSAGE,
                }
                return

            try:
                strategy = get_strategy(
                    selection.configuration, llm_factory=self._llm_factory
                )
            except ConfigurationNotImplemented as e:
                # No agent is contacted and no run directory is created.
                yield {"type": "status", "state": "not_implemented", "message": str(e)}
                return

            run_id = new_run_id()
            queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
            moderator = Moderator(
                run_id=run_id,
                case=selection.case,
                configuration=selection.configuration,
                transport=self._transport,
                buyer=self._buyer,
                limits=self._limits,
                run_dir=self._run_root / run_id,
                emit=queue.put_nowait,
                meta={
                    "model": self._model,
                    "l9_available": self.l9_enabled,
                    "selection": selection.sources,
                    "prompt": prompt,
                },
            )
            task = asyncio.create_task(moderator.run(strategy))
            task.add_done_callback(lambda _t: queue.put_nowait(None))
            try:
                while (event := await queue.get()) is not None:
                    yield event
                await task  # surfaces an unexpected failure to the caller
            finally:
                if not task.done():
                    task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await task
        finally:
            detach_workflow_context(token)

    async def run(
        self,
        prompt: str,
        *,
        case: str | None = None,
        configuration: str | None = None,
        workflow_instance_id: str | None = None,
    ) -> dict[str, Any]:
        """Run to the end and return the selection, record and verdict."""
        result: dict[str, Any] = {"messages": 0}
        async for event in self.stream(
            prompt,
            case=case,
            configuration=configuration,
            workflow_instance_id=workflow_instance_id,
        ):
            kind = event["type"]
            if kind == "message":
                result["messages"] += 1
            elif kind == "status" and event["state"] in (
                "selected",
                "not_implemented",
                "l9_disabled",
            ):
                result[event["state"]] = event
            elif kind in ("record", "verdict"):
                result[kind] = event[kind]
        return result
