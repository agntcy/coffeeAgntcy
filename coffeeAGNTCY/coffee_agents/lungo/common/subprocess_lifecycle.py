# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Graceful shutdown for agent/MCP subprocesses (SIGTERM from integration tests)."""

from __future__ import annotations

import asyncio
import logging
import signal
from contextlib import suppress
from typing import Protocol


class AppSessionLifecycle(Protocol):
    """SDK app session contract used by ``run_until_shutdown``."""

    async def start_all_sessions(self, *, keep_alive: bool) -> None: ...

    async def stop_all_sessions(self) -> None: ...


async def run_until_shutdown(
    app_session: AppSessionLifecycle,
    *,
    logger: logging.Logger,
) -> None:
    """
    Run ``start_all_sessions(keep_alive=True)`` until SIGTERM/SIGINT, then stop sessions.

    Call after the agent has logged "Agent ready" (initial ``keep_alive=False`` start).
    """
    shutdown = asyncio.Event()

    def request_shutdown() -> None:
        logger.info("Shutting down gracefully on signal")
        shutdown.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, request_shutdown)
        except (NotImplementedError, ValueError):
            signal.signal(sig, lambda _signum, _frame: request_shutdown())

    keep_alive_task = asyncio.create_task(
        app_session.start_all_sessions(keep_alive=True),
        name="app_session_keep_alive",
    )
    await shutdown.wait()
    keep_alive_task.cancel()
    with suppress(asyncio.CancelledError):
        await keep_alive_task
    await app_session.stop_all_sessions()
