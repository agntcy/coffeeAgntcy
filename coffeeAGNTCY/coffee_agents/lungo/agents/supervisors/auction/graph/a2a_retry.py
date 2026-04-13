# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""A2A send_message retry with exponential backoff and timeout/no-payload error classification.

The A2A SDK (>=0.3.x) ``client.send_message(message)`` returns an
``AsyncIterator[ClientEvent | Message]``.  This module is intentionally
agnostic to the event types — it collects whatever the stream yields,
decides success/failure based on whether *anything* was produced, and
leaves interpretation to the caller.
"""

import asyncio
import logging

_SENTINEL = object()
_SLIM_ERROR = None


def _get_slim_error():
    global _SLIM_ERROR
    if _SLIM_ERROR is None:
        try:
            from slim_bindings import SlimError
            _SLIM_ERROR = SlimError
        except ImportError:
            pass
    return _SLIM_ERROR


class TransportTimeoutError(Exception):
    """Wraps the cause when the last attempt failed with a timeout (e.g. SLIM receive timeout)."""
    def __init__(self, message: str, cause: BaseException | None = None):
        super().__init__(message)
        self.__cause__ = cause


class RemoteAgentNoResponseError(Exception):
    """Wraps the cause when the remote returns no usable response (missing or invalid payload)."""
    def __init__(self, message: str, cause: BaseException | None = None):
        super().__init__(message)
        self.__cause__ = cause


def _is_timeout_error(exc: BaseException, slim_error_class: type | None = _SENTINEL) -> bool:
    """True iff the exception is SlimError.SessionError or AttributeError with SlimError.SessionError in chain (SDK wrap)."""
    if slim_error_class is _SENTINEL:
        SlimError = _get_slim_error()
    else:
        SlimError = slim_error_class
    if SlimError is None:
        return False
    if isinstance(exc, SlimError.SessionError):
        return True
    if not isinstance(exc, AttributeError):
        return False
    seen = set()
    current = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, SlimError.SessionError):
            return True
        current = getattr(current, "__cause__", None) or getattr(current, "__context__", None)
    return False


def _is_no_payload_error(exc: BaseException) -> bool:
    """True iff the exception is an AttributeError for missing 'payload' (e.g. access on None)."""
    return isinstance(exc, AttributeError) and getattr(exc, "name", None) == "payload"


_A2A_MAX_ATTEMPTS = 5
_A2A_BACKOFF_BASE = 3

logger = logging.getLogger(__name__)


async def send_a2a_with_retry(client, message, context=None):
    """
    Iterate ``client.send_message(message)`` to completion with retry on
    transient failures.

    On timeout or empty stream, retries up to 4 times (5 attempts total)
    with exponential backoff (base 3, delays 1s, 3s, 9s, 27s).

    Args:
        client: The A2A client instance.
        message: The Message to send.
        context: Optional ``ClientCallContext`` forwarded to
                 ``client.send_message`` so interceptors can access
                 caller-provided metadata (correlation_id, instance_id, etc.).

    Returns:
        list: The collected events from the stream (``ClientEvent | Message``).
              Callers are responsible for interpreting the contents.
    """
    for attempt in range(_A2A_MAX_ATTEMPTS):
        try:
            events = []
            async for event in client.send_message(message, context=context):
                events.append(event)

            if events:
                return events

            # Stream completed but yielded nothing — treat as no-response.
            if attempt < _A2A_MAX_ATTEMPTS - 1:
                delay = _A2A_BACKOFF_BASE ** attempt
                logger.warning(
                    "A2A request had no response, retrying (attempt %s/%s) after %ss.",
                    attempt + 2,
                    _A2A_MAX_ATTEMPTS,
                    delay,
                )
                await asyncio.sleep(delay)
                continue
            raise RemoteAgentNoResponseError(
                "Remote agent returned no response (empty stream).",
                cause=None,
            )
        except RemoteAgentNoResponseError:
            raise
        except Exception as e:
            if _is_timeout_error(e):
                if attempt < _A2A_MAX_ATTEMPTS - 1:
                    delay = _A2A_BACKOFF_BASE ** attempt
                    logger.warning(
                        "A2A request timed out, retrying (attempt %s/%s) after %ss.",
                        attempt + 2,
                        _A2A_MAX_ATTEMPTS,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise TransportTimeoutError(
                    "Remote agent did not respond in time (SLIM receive timeout).",
                    cause=e,
                ) from e
            if _is_no_payload_error(e):
                if attempt < _A2A_MAX_ATTEMPTS - 1:
                    delay = _A2A_BACKOFF_BASE ** attempt
                    logger.warning(
                        "A2A request had no response, retrying (attempt %s/%s) after %ss.",
                        attempt + 2,
                        _A2A_MAX_ATTEMPTS,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise RemoteAgentNoResponseError(
                    "Remote agent returned no response (missing or invalid payload).",
                    cause=e,
                ) from e
            logger.error("A2A send_message failed: %s", e)
            raise

