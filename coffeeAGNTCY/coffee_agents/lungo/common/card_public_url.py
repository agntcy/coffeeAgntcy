# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Advertise a dialable HTTP address for an agent that serves JSON-RPC.

The app SDK reads the address its HTTP server binds to from the card's JSONRPC
interface URL, which is why the farm cards say ``http://0.0.0.0:<port>``. That
is a listen address, not a destination, so the copy of the card that is served
to clients gets the host in ``FARM_AGENT_HOST`` instead (same port and path).
"""

import logging
import os
from urllib.parse import urlsplit, urlunsplit

from a2a.types import AgentCard
from agntcy_app_sdk.semantic.a2a.card_utils import clone_card
from agntcy_app_sdk.semantic.a2a.transport_types import normalize_transport

logger = logging.getLogger(__name__)

_WILDCARD_HOSTS = frozenset({"", "0.0.0.0", "::"})
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _in_container() -> bool:
    """True inside a Docker container or a Kubernetes pod."""
    return os.path.exists("/.dockerenv") or bool(os.getenv("KUBERNETES_SERVICE_HOST"))


def with_public_http_host(card: AgentCard, host: str) -> AgentCard:
    """Return a copy of ``card`` whose JSONRPC interfaces advertise ``host``.

    Only interfaces whose host is a wildcard (``0.0.0.0``, ``::`` or empty) are
    rewritten, keeping scheme, port, path and query. The input card is left
    untouched because it is also the source of the bind address.

    Logs a warning when the advertised host is a loopback name inside a
    container or pod, where only the agent itself can reach it.
    """
    if not host or host in _WILDCARD_HOSTS:
        raise ValueError(
            f"FARM_AGENT_HOST {host!r} is not an address clients can dial. "
            "Use a resolvable host name, for example the compose service name."
        )
    served = clone_card(card)
    for interface in served.supported_interfaces:
        if normalize_transport(interface.protocol_binding) != "jsonrpc":
            continue
        parts = urlsplit(interface.url)
        if (parts.hostname or "") not in _WILDCARD_HOSTS:
            continue
        netloc = f"{host}:{parts.port}" if parts.port else host
        interface.url = urlunsplit(
            (parts.scheme, netloc, parts.path, parts.query, parts.fragment)
        )
        if host in _LOOPBACK_HOSTS and _in_container():
            logger.warning(
                "Advertising %s for the HTTP interface, which only this container "
                "can reach. Set FARM_AGENT_HOST to the name other services use.",
                interface.url,
            )
    return served
