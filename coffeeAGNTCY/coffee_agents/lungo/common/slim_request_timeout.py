# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Widen the deadline the app SDK applies to SLIM request/reply exchanges, and
report it when it expires."""

from __future__ import annotations

import functools
import inspect
import logging

from agntcy_app_sdk.transport.slim.transport import SLIMTransport

logger = logging.getLogger(__name__)

_APPLIED_TIMEOUT = "_coffee_agntcy_slim_request_timeout"


def apply_slim_request_timeout(timeout_seconds: int) -> None:
    """Default ``SLIMTransport.request()`` to ``timeout_seconds``.

    agntcy-app-sdk keeps the deadline in the signature of
    ``SLIMTransport.request()`` (default 6s) and its A2A client never forwards
    one; ``SlimTransportConfig.message_timeout_seconds`` applies to listening
    sessions, not to ``request()``, so config offers no way to raise it.
    Replacing the method is the only hook available; drop this module once the
    SDK takes the value as config.

    The SDK now raises ``asyncio.TimeoutError`` itself when the deadline lapses.
    Older SDKs (0.5.5) logged the expiry and returned ``None``, so callers only
    found out through an ``AttributeError`` on the missing payload; the override
    still raises ``TimeoutError`` on a ``None`` reply as a backstop for those.

    Callers that pass their own ``timeout`` are left untouched, and the override
    is skipped altogether if a future SDK stops accepting the argument.
    """
    if timeout_seconds <= 0:
        raise ValueError(
            f"SLIM request timeout must be positive, got {timeout_seconds}"
        )

    current = SLIMTransport.request
    if getattr(current, _APPLIED_TIMEOUT, None) == timeout_seconds:
        return

    original = inspect.unwrap(current)
    if "timeout" not in inspect.signature(original).parameters:
        logger.warning(
            "SLIMTransport.request() no longer accepts a timeout; "
            "keeping the SDK default instead of applying %ss.",
            timeout_seconds,
        )
        return

    @functools.wraps(original)
    async def request(self, recipient, message, *args, **kwargs):
        if not args:
            kwargs.setdefault("timeout", timeout_seconds)
        deadline = args[0] if args else kwargs["timeout"]
        reply = await original(self, recipient, message, *args, **kwargs)
        if reply is None:
            raise TimeoutError(f"No SLIM reply from {recipient} within {deadline}s.")
        return reply

    setattr(request, _APPLIED_TIMEOUT, timeout_seconds)
    SLIMTransport.request = request
    logger.info("SLIM request/reply deadline set to %ss.", timeout_seconds)
