# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from urllib.parse import urlparse

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from dotenv import load_dotenv

load_dotenv()

# The URL clients use to reach the recruiter, as published in its card. It is
# not the address the server binds to (see server.py), so it must be a host that
# other containers or machines can resolve, for example http://recruiter:8881.
# An empty value (a Helm chart that leaves it unset renders an empty variable)
# falls back to the default.
RECRUITER_AGENT_URL = os.getenv("RECRUITER_AGENT_URL") or "http://localhost:8881"

_WILDCARD_HOSTS = frozenset({"", "0.0.0.0", "::"})
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _in_container() -> bool:
    """True inside a Docker container or a Kubernetes pod."""
    return os.path.exists("/.dockerenv") or bool(os.getenv("KUBERNETES_SERVICE_HOST"))


def check_advertised_url(url: str) -> str | None:
    """Reject an advertised URL no client can dial and flag one that is suspect.

    Raises ``ValueError`` for a wildcard host (``0.0.0.0``, ``::`` or none):
    that is a listen address, not a destination. Returns a warning message when
    the host is a loopback name inside a container or pod, where only the
    recruiter itself can reach it, and ``None`` when the URL looks fine.
    """
    host = urlparse(url).hostname or ""
    if host in _WILDCARD_HOSTS:
        raise ValueError(
            f"RECRUITER_AGENT_URL {url!r} is not an address clients can dial. "
            "Use a resolvable host name, for example http://recruiter:8881; "
            "the listen address is set separately with RECRUITER_BIND_HOST."
        )
    if host in _LOOPBACK_HOSTS and _in_container():
        return (
            f"RECRUITER_AGENT_URL {url!r} points at the loopback interface, so "
            "only this container can reach the address in the agent card. Set "
            "RECRUITER_AGENT_URL to the name other services use for the recruiter."
        )
    return None


# Define A2A agent card
AGENT_CARD = AgentCard(
    name="RecruiterAgent",
    description="An agent that helps find and recruit other agents based on specified criteria.",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=True),
    skills=[
        AgentSkill(
            id="recruit_agents",
            name="Recruit agents",
            description="Search the agent directory for agents that match a task and evaluate them against scenarios.",
            tags=["recruiting", "agents", "evaluation"],
        )
    ],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    supported_interfaces=[
        # jsonrpc endpoint for direct client-agent communication over http
        AgentInterface(
            protocol_binding="JSONRPC",
            url=RECRUITER_AGENT_URL,
            protocol_version="1.0",
        ),
    ],
)
