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

    Returns once a shutdown signal arrives or the keep-alive session ends on its
    own; re-raises if the keep-alive session fails. Call after the agent has
    logged "Agent ready" (initial ``keep_alive=False`` start).
    """
    shutdown = asyncio.Event()

    def request_shutdown() -> None:
        logger.info("Shutting down gracefully on signal")
        shutdown.set()

    def handle_signal(_signum: int, _frame: object) -> None:
        request_shutdown()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, request_shutdown)
        except (NotImplementedError, ValueError):
            try:
                signal.signal(sig, handle_signal)
            except ValueError as exc:
                logger.error("Could not register handler for %s: %s", sig, exc)

    keep_alive_task = asyncio.create_task(
        app_session.start_all_sessions(keep_alive=True),
        name="app_session_keep_alive",
    )
    shutdown_task = asyncio.create_task(shutdown.wait(), name="app_session_shutdown")
    try:
        await asyncio.wait(
            {keep_alive_task, shutdown_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
    finally:
        shutdown_task.cancel()
        with suppress(asyncio.CancelledError):
            await shutdown_task

    if not keep_alive_task.done():
        keep_alive_task.cancel()

    keep_alive_error: Exception | None = None
    try:
        await keep_alive_task
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        keep_alive_error = exc

    # Best-effort cleanup, then surface a keep-alive failure if it ended on its own.
    await app_session.stop_all_sessions()
    if keep_alive_error is not None:
        raise keep_alive_error
