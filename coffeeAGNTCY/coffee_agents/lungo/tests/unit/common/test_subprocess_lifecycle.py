# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for graceful agent subprocess shutdown."""

from __future__ import annotations

import asyncio
import logging
import signal
from unittest.mock import AsyncMock, patch

import pytest

from common.subprocess_lifecycle import run_until_shutdown


async def _block_until_cancelled(*, keep_alive: bool) -> None:
    """Stand-in for a real keep-alive session that runs until cancelled."""
    await asyncio.Event().wait()


SHUTDOWN_CASES = [
    pytest.param(
        False,
        None,
        None,
        None,
        id="loop add_signal_handler path cancels keep-alive and stops",
    ),
    pytest.param(
        True,
        None,
        None,
        None,
        id="signal.signal fallback path registers SIGTERM and stops",
    ),
    pytest.param(
        False,
        None,
        RuntimeError("stop failed"),
        RuntimeError,
        id="stop_all_sessions error propagates",
    ),
    pytest.param(
        False,
        RuntimeError("keep-alive failed"),
        None,
        RuntimeError,
        id="keep-alive failure still stops then propagates",
    ),
]


@pytest.mark.parametrize(
    ("use_signal_fallback", "start_error", "stop_error", "expected_error"),
    SHUTDOWN_CASES,
)
async def test_run_until_shutdown(
    use_signal_fallback: bool,
    start_error: Exception | None,
    stop_error: Exception | None,
    expected_error: type[Exception] | None,
) -> None:
    """``run_until_shutdown`` registers a handler, then stops sessions on signal."""
    session = AsyncMock()
    if start_error is not None:
        session.start_all_sessions.side_effect = start_error
    else:
        session.start_all_sessions.side_effect = _block_until_cancelled
    if stop_error is not None:
        session.stop_all_sessions.side_effect = stop_error

    handlers: dict[int, object] = {}

    def capture_loop_handler(sig: int, callback: object) -> None:
        if use_signal_fallback:
            raise NotImplementedError
        handlers[sig] = callback

    def capture_signal_handler(sig: int, handler: object) -> None:
        handlers[sig] = handler

    loop = asyncio.get_running_loop()
    with (
        patch.object(loop, "add_signal_handler", side_effect=capture_loop_handler),
        patch(
            "common.subprocess_lifecycle.signal.signal",
            side_effect=capture_signal_handler,
        ),
    ):
        task = asyncio.create_task(
            run_until_shutdown(session, logger=logging.getLogger("test")),
        )
        await asyncio.sleep(0)
        assert signal.SIGTERM in handlers

        # A failing keep-alive ends on its own; otherwise a signal drives shutdown.
        if start_error is None:
            trigger = handlers[signal.SIGTERM]
            if use_signal_fallback:
                trigger(signal.SIGTERM, None)
            else:
                trigger()

        if expected_error is not None:
            with pytest.raises(expected_error):
                await asyncio.wait_for(task, timeout=2.0)
        else:
            await asyncio.wait_for(task, timeout=2.0)

    session.start_all_sessions.assert_awaited_once_with(keep_alive=True)
    session.stop_all_sessions.assert_awaited_once()
