# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Opt the A2A servers into the app SDK's placeholder SLIM secret for local demos."""

from __future__ import annotations

from typing import Any, TypeVar

import config.config
from agntcy_app_sdk import CardBuilder

_Builder = TypeVar("_Builder", bound=CardBuilder)

_SECRET_ERROR_PREFIX = "SLIM shared secret required"


def apply_placeholder_secret_policy(builder: _Builder) -> _Builder:
    """Allow the placeholder SLIM secret on ``builder`` if SLIM_ALLOW_PLACEHOLDER_SECRET is set.

    ``CardBuilder.start()`` raises for a ``slimpatterns`` or ``slimrpc``
    interface when SLIM_SHARED_SECRET is unset or is the SDK's public
    placeholder, unless ``allow_placeholder_secret()`` was called. The flag is
    the value ``config.config`` parsed at import (after ``load_dotenv``); it is
    looked up on each call so tests can patch it. A real secret is used whether
    or not the flag is set.
    """
    if config.config.SLIM_ALLOW_PLACEHOLDER_SECRET:
        return builder.allow_placeholder_secret()
    return builder


async def start_builder(builder: CardBuilder, **kwargs: Any) -> None:
    """Start ``builder``, replacing the SDK's missing-secret advice with the corto settings.

    The SDK tells the caller to use ``.allow_placeholder_secret()``; corto
    operators set ``SLIM_ALLOW_PLACEHOLDER_SECRET`` instead. Other errors
    propagate unchanged.
    """
    try:
        await builder.start(**kwargs)
    except ValueError as exc:
        if not str(exc).startswith(_SECRET_ERROR_PREFIX):
            raise
        cause = str(exc).partition(". Use ")[0]
        raise ValueError(
            f"{cause}. Set SLIM_SHARED_SECRET, or SLIM_ALLOW_PLACEHOLDER_SECRET=true "
            "for a local demo."
        ) from exc
