# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Top-level classification for propagation: timeout (504), unexpected packet / no payload (502), other (500)."""

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

