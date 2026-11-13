# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
A2A protocol record parser.

Parses A2A AgentCard JSON records into AgentEvalConfig for evaluation.
Handles both strict A2A AgentCard schemas and looser AGNTCY directory
records that may be missing required AgentCard fields.
"""

import copy
import json
import os
from typing import Union
from urllib.parse import urlsplit, urlunsplit

from a2a.client.card_resolver import parse_agent_card
from a2a.types import AgentCard
from rogue_sdk.types import AuthType, Protocol, Transport

from agent_recruiter.common.logging import get_logger
from agent_recruiter.interviewers.models import AgentEvalConfig

logger = get_logger(__name__)

# Hosts an agent publishes for its own bind address. From the recruiter they
# point at the recruiter itself, so the card fetch would fail.
_UNROUTABLE_ADVERTISED_HOSTS = frozenset(
    {"0.0.0.0", "::", "127.0.0.1", "::1", "localhost"}
)

_DISCOVERED_ADDRESSES_ENV = "RECRUITER_DISCOVERED_AGENT_ADDRESSES"


def _discovered_address_overrides() -> dict[int, str]:
    """Read ``RECRUITER_DISCOVERED_AGENT_ADDRESSES`` into ``{advertised port: netloc}``.

    The value is a comma-separated list of ``PORT=HOST[:PORT]`` pairs, for
    example ``9998=colombia-farm:9999``. ``PORT`` is the port in the record,
    ``HOST[:PORT]`` is where the agent can be reached from the recruiter. A
    target without a port keeps the advertised port. An entry that does not
    parse is logged and skipped, so one typo does not disable the others. The
    variable is read on every call, like ``RECRUITER_DISCOVERED_AGENT_HOST``.
    """
    overrides: dict[int, str] = {}
    for entry in (os.getenv(_DISCOVERED_ADDRESSES_ENV) or "").split(","):
        entry = entry.strip()
        if not entry:
            continue
        advertised, _, target = (part.strip() for part in entry.partition("="))
        try:
            if not advertised.isdigit():
                raise ValueError("the part before '=' must be a port number")
            parsed = urlsplit(f"//{target}")
            if (
                not parsed.hostname
                or parsed.netloc != target
                or parsed.username is not None
            ):
                raise ValueError("the part after '=' must be HOST or HOST:PORT")
            target_port = parsed.port  # Raises ValueError for an invalid port.
        except ValueError as err:
            logger.warning(
                "Ignoring {} entry {!r}: {}", _DISCOVERED_ADDRESSES_ENV, entry, err
            )
            continue
        overrides[int(advertised)] = (
            target if target_port is not None else f"{target}:{advertised}"
        )
    return overrides


def _reachable_url(url: str) -> str:
    """Replace a bind or loopback host in ``url`` with an address the recruiter can dial.

    Directory records of agents that listen on every interface carry URLs such
    as ``http://0.0.0.0:9998``. The evaluator fetches the agent card from the
    URL it is given, so it needs an address that reaches the agent from where
    the recruiter runs. Two settings decide it:

    * ``RECRUITER_DISCOVERED_AGENT_ADDRESSES`` maps the port of the record to
      the host and port of one agent, for deployments where each agent has its
      own host or a different port (for example one Kubernetes Service per
      farm). It wins when it has the port of the url.
    * ``RECRUITER_DISCOVERED_AGENT_HOST`` replaces only the host and keeps the
      port (for example ``host.docker.internal`` for agents whose ports are
      published on the Docker host). It defaults to ``localhost``, which
      leaves a loopback host as it is.

    The scheme, path and query are kept. Non-HTTP urls (``slim://``,
    ``nats://``) and other hosts are returned unchanged. Both variables are
    read on every call.
    """
    if not url:
        return url
    parts = urlsplit(url)
    if parts.scheme.lower() not in ("http", "https"):
        return url
    if parts.hostname not in _UNROUTABLE_ADVERTISED_HOSTS:
        return url
    netloc = _discovered_address_overrides().get(parts.port) if parts.port else None
    if netloc is None:
        host = os.getenv("RECRUITER_DISCOVERED_AGENT_HOST") or "localhost"
        netloc = f"{host}:{parts.port}" if parts.port else host
    rewritten = urlunsplit(
        (parts.scheme, netloc, parts.path, parts.query, parts.fragment)
    )
    if rewritten != url:
        logger.debug("Rewrote advertised agent url {} to {}", url, rewritten)
    return rewritten


def _parse_card(record: dict) -> AgentCard:
    """Parse ``record`` as an ``AgentCard``, accepting the v0.3 and v1.x shapes.

    ``parse_agent_card`` maps the v0.3 connection fields (``url``,
    ``preferredTransport``, ``additionalInterfaces``) to
    ``supportedInterfaces`` and ignores unknown fields. It edits the dict it is
    given, so it gets a copy.
    """
    return parse_agent_card(copy.deepcopy(record))


def _card_url(card: AgentCard) -> str:
    """URL of the card's first JSON-RPC interface, else of its first HTTP interface.

    SLIM and NATS urls are not returned: the evaluator dials HTTP only, and a
    ``slim://`` url would fail later with an unclear httpx error.
    """
    interfaces = list(card.supported_interfaces)
    for interface in interfaces:
        if interface.protocol_binding.upper() == "JSONRPC" and interface.url:
            return interface.url
    return next(
        (i.url for i in interfaces if i.url.startswith(("http://", "https://"))), ""
    )


def _extract_from_dict(record: dict) -> AgentEvalConfig:
    """Manually extract evaluation config from a raw agent record dict.

    This handles AGNTCY directory records that do not conform to the strict
    A2A ``AgentCard`` schema (e.g. missing ``capabilities``,
    ``defaultInputModes``, or having a different skills structure).

    Args:
        record: Dict containing agent data.

    Returns:
        AgentEvalConfig with extracted agent information.

    Raises:
        ValueError: If the record is missing a ``url`` field.
    """
    url = record.get("url", "")
    name = record.get("name", "Unknown")
    description = record.get("description", "")

    if not url:
        raise ValueError(
            f"Agent record for '{name}' is missing a 'url' field - "
            "cannot evaluate an agent without a reachable endpoint."
        )

    return AgentEvalConfig(
        protocol=Protocol.A2A,
        transport=Transport.HTTP,
        evaluated_agent_url=_reachable_url(url),
        auth_type=AuthType.NO_AUTH,
        auth_credentials=None,
        agent_name=name,
        agent_description=description,
    )


def parse_a2a_agent_record(raw_json: Union[str, dict]) -> AgentEvalConfig:
    """Parse an A2A agent record into AgentEvalConfig.

    First attempts strict ``AgentCard`` validation.  If that fails (e.g. the
    record comes from the AGNTCY directory and is missing fields like
    ``capabilities`` or ``defaultInputModes``), falls back to manual field
    extraction which only requires ``url`` and ``name``.

    Args:
        raw_json: Either a JSON string or dict containing agent data.

    Returns:
        AgentEvalConfig with extracted agent information.

    Raises:
        ValueError: If neither parsing strategy can extract a usable config.
    """
    logger.debug("Parsing A2A agent record")

    # Normalise to dict
    if isinstance(raw_json, str):
        try:
            record_dict = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in agent record: {e}") from e
    else:
        record_dict = raw_json

    # --- Try AgentCard parsing first ---
    # Python deletes ``strict_err`` when its ``except`` block ends, so keep the
    # error for the message the fallback path raises.
    strict_error: Exception | None = None
    try:
        agent_card = _parse_card(record_dict)

        logger.info(f"Successfully parsed AgentCard for agent: {agent_card.name}")

        card_url = _reachable_url(_card_url(agent_card))
        if not card_url:
            raise ValueError("AgentCard has no interface with a 'url'")

        config = AgentEvalConfig(
            protocol=Protocol.A2A,
            transport=Transport.HTTP,
            evaluated_agent_url=card_url,
            auth_type=AuthType.NO_AUTH,
            auth_credentials=None,
            agent_name=agent_card.name or "Unknown",
            agent_description=agent_card.description,
        )

        logger.info(
            "Parsed A2A agent record (strict)",
            extra={"agent_name": agent_card.name, "url": card_url},
        )
        return config

    except Exception as strict_err:
        strict_error = strict_err
        logger.debug(
            "Strict AgentCard validation failed ({}), falling back to manual extraction",
            strict_err,
        )

    # --- Fallback: manual extraction from raw dict ---
    try:
        config = _extract_from_dict(record_dict)
        logger.info(
            "Parsed A2A agent record (fallback)",
            extra={
                "agent_name": config.agent_name,
                "url": config.evaluated_agent_url,
            },
        )
        return config

    except ValueError:
        raise
    except Exception as fallback_err:
        raise ValueError(
            f"Could not parse agent record: strict={strict_error}, fallback={fallback_err}"
        ) from fallback_err
