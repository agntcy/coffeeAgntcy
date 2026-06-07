# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for graceful agent subprocess shutdown."""

from __future__ import annotations

import asyncio
import logging
import signal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from common.subprocess_lifecycle import run_until_shutdown


@pytest.mark.asyncio
async def test_run_until_shutdown_stops_session_on_signal() -> None:
    """SIGTERM handler cancels keep-alive and awaits stop_all_sessions."""
    session = AsyncMock()
    shutdown_handlers: dict[int, object] = {}
    loop = asyncio.get_running_loop()

    def capture_handler(sig: int, callback: object) -> None:
        shutdown_handlers[sig] = callback

    with patch.object(loop, "add_signal_handler", side_effect=capture_handler):
        task = asyncio.create_task(
            run_until_shutdown(session, logger=logging.getLogger("test")),
        )
        await asyncio.sleep(0)
        assert signal.SIGTERM in shutdown_handlers
        shutdown_handlers[signal.SIGTERM]()
        await asyncio.wait_for(task, timeout=2.0)

    session.start_all_sessions.assert_awaited_once_with(keep_alive=True)
    session.stop_all_sessions.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_until_shutdown_uses_signal_module_when_add_handler_unsupported() -> None:
    """Fallback path registers handlers via signal.signal."""
    session = AsyncMock()
    registered: list[tuple[int, object]] = []

    def fake_signal(sig: int, handler: object) -> None:
        registered.append((sig, handler))

    loop = asyncio.get_running_loop()
    with (
        patch.object(
            loop,
            "add_signal_handler",
            side_effect=NotImplementedError,
        ),
        patch("common.subprocess_lifecycle.signal.signal", side_effect=fake_signal),
    ):
        task = asyncio.create_task(
            run_until_shutdown(session, logger=logging.getLogger("test")),
        )
        await asyncio.sleep(0)
        assert any(sig == signal.SIGTERM for sig, _ in registered)
        handler = next(h for sig, h in registered if sig == signal.SIGTERM)
        handler(signal.SIGTERM, None)
        await asyncio.wait_for(task, timeout=2.0)

    session.stop_all_sessions.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_until_shutdown_propagates_stop_errors() -> None:
    """Errors from stop_all_sessions are not swallowed."""
    session = MagicMock()
    session.start_all_sessions = AsyncMock()
    session.stop_all_sessions = AsyncMock(side_effect=RuntimeError("stop failed"))
    loop = asyncio.get_running_loop()
    shutdown_handlers: dict[int, object] = {}

    def capture_handler(sig: int, callback: object) -> None:
        shutdown_handlers[sig] = callback

    with patch.object(loop, "add_signal_handler", side_effect=capture_handler):
        task = asyncio.create_task(
            run_until_shutdown(session, logger=logging.getLogger("test")),
        )
        await asyncio.sleep(0)
        shutdown_handlers[signal.SIGTERM]()
        with pytest.raises(RuntimeError, match="stop failed"):
            await asyncio.wait_for(task, timeout=2.0)
