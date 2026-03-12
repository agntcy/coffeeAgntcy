# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Agentic pattern definitions — describes *what* a communication pattern
looks like in terms of protocol, transport, and topology (node graph).

Serving details (ports, sessions, connections) are handled by each agent.

Patterns are primarily a frontend contract — the UI renders and provides
an interface for any pattern defined here.  On the code side, patterns
serve as a **config lookup** for transport preference: tool code can
query the :data:`PATTERNS` registry to read the transport, protocol,
communication channel, or agent list for a given pattern, then pass
that as a preference to the A2A client factory for negotiation::

    from common.agentic_patterns import PATTERNS

    # Look up the enabled publish-subscribe variant (slim or nats)
    pattern = PATTERNS.resolve("publish-subscribe")
    card = remote_agent_card.model_copy()
    card.preferred_transport = pattern.transport.value
    client = await factory.create(card)
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Pattern Enums
# ──────────────────────────────────────────────

class ProtocolType(str, Enum):
    """Wire protocol for agent-to-agent communication."""
    A2A = "a2a"
    MCP = "mcp"


class TransportType(str, Enum):
    """Transport mechanism understood by AgntcyFactory.create_transport()."""
    SLIM_RPC = "slimrpc"
    SLIM = "slim"
    NATS = "nats"
    HTTP = "http"


class NodeRole(str, Enum):
    """Logical role a node plays in a pattern topology."""
    SUPERVISOR = "supervisor"
    MODERATOR = "moderator"
    WORKER = "worker"
    MEMBER = "member"
    CLIENT = "client"
    SERVER = "server"


class AgentRecordFormat(str, Enum):
    """Format of the agent record that a topology node references."""
    OASF = "oasf"          # OASF JSON agent record
    A2A_CARD = "a2a_card"  # A2A AgentCard (Python module or JSON)


# ──────────────────────────────────────────────
# Topology — a directed graph of nodes and edges
# ──────────────────────────────────────────────


class TopologyNode(BaseModel):
    """A participant slot in the pattern."""
    id: str = Field(description="Unique node identifier within the pattern, e.g. 'supervisor', 'farm_a'")
    role: NodeRole
    description: str = ""


class TopologyEdge(BaseModel):
    """A directed communication link between two nodes."""
    source: str = Field(description="id of the sending node")
    target: str = Field(description="id of the receiving node")
    description: str = ""


class Topology(BaseModel):
    """
    Graph representation of how agents interact within a pattern.

    Nodes are role-slots (not concrete agent instances); edges describe
    the allowed/expected communication directions.
    """
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]


# ──────────────────────────────────────────────
# UI placeholder — to be expanded in a later epic
# ──────────────────────────────────────────────

class UIHint(BaseModel):
    """Opaque placeholder for future UI metadata."""
    display_name: str = ""
    sub_label: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)


# ──────────────────────────────────────────────
# Agent reference — points to an agent record (OASF JSON or A2A AgentCard)
# ──────────────────────────────────────────────

class AgentRef(BaseModel):
    """
    Reference to an agent's record.

    Points to either an OASF JSON file or an A2A AgentCard module.
    The path is relative to the project root.
    """
    name: str = Field(description="Human-readable agent name, e.g. 'Brazil Coffee Farm'")
    format: AgentRecordFormat
    path: str = Field(description="Relative path to the agent record, e.g. 'agents/supervisors/auction/oasf/agents/brazil-coffee-farm.json'")


# ──────────────────────────────────────────────
# Core pattern config
# ──────────────────────────────────────────────

class AgenticPatternConfig(BaseModel):
    """
    Defines an agentic communication pattern.

    Agents look up a pattern by id to understand what protocol, transport,
    and topology shape they are participating in.  Everything about *how*
    to actually serve (ports, sessions, credentials) lives in each agent's
    own server code.
    """
    id: str = Field(description="Canonical identifier, e.g. 'slim-rpc'")
    enabled: bool = Field(default=True, description="Whether this pattern is active and should be used for transport negotiation. Set to False to disable a pattern without deleting its config.")
    name: str
    description: str

    protocol: ProtocolType
    transport: TransportType
    agents: List[AgentRef] = Field(
        default_factory=list,
        description="Agents that participate in this pattern, independent of topology."
    )
    communication_channel: Optional[str] = Field(
        default=None,
        description="Optional identifier for the communication channel (e.g. pub/sub topic) that agents should use when communicating with each other. This is transport-specific and may be ignored by some transports."
    )

    topology: Optional[Topology] = Field(
        default=None,
        description="Graph of how agents interact. None when topology is dynamic or not yet defined."
    )

    ui_hint: UIHint = Field(default_factory=UIHint)
    metadata: Dict[str, str] = Field(default_factory=dict)

    def __str__(self):
        return f"AgenticPatternConfig(id={self.id}, protocol={self.protocol}, transport={self.transport})"
    
    def from_file(self, file_path: str) -> "AgenticPatternConfig":
        raise NotImplementedError("from_file is not implemented yet. This is a placeholder for future deserialization logic from a file source.")
    
    def to_file(self, file_path: str, is_json: bool = True, is_yaml: bool = False) -> None:
        raise NotImplementedError("to_file is not implemented yet. This is a placeholder for future serialization logic to a file source.")
    
    def to_json(self) -> str:
        raise NotImplementedError("to_json is not implemented yet. This is a placeholder for future serialization logic to JSON string.")


# ──────────────────────────────────────────────
# Registry
# ──────────────────────────────────────────────

class PatternRegistry:
    """Lookup over registered agentic patterns."""

    def __init__(self, patterns: List[AgenticPatternConfig] | None = None):
        self._by_id: Dict[str, AgenticPatternConfig] = {}
        for p in (patterns or []):
            self.register(p)

    @classmethod
    def from_file(cls, path: str) -> "PatternRegistry":
        """Load patterns from a YAML file.

        The file must contain a top-level ``patterns`` key with a list of
        pattern objects that conform to :class:`AgenticPatternConfig`.
        YAML anchors/aliases (e.g. ``_agent_defs``, ``_farm_agents``) are
        resolved automatically by the YAML parser and ignored at the
        top level.
        """
        raw = yaml.safe_load(Path(path).read_text())
        if not isinstance(raw, dict) or "patterns" not in raw:
            raise ValueError(f"YAML file must contain a top-level 'patterns' key: {path}")
        patterns = [AgenticPatternConfig(**p) for p in raw["patterns"]]
        return cls(patterns)

    def register(self, pattern: AgenticPatternConfig) -> None:
        """Add a pattern to the registry. Raises on duplicate ids."""
        if pattern.id in self._by_id:
            raise ValueError(
                f"Duplicate pattern id: {pattern.id!r}. "
                f"Already registered: {self._by_id[pattern.id].name!r}"
            )
        self._by_id[pattern.id] = pattern

    def get(self, pattern_id: str) -> AgenticPatternConfig:
        try:
            return self._by_id[pattern_id]
        except KeyError:
            raise KeyError(
                f"Unknown agentic pattern: {pattern_id!r}. "
                f"Available: {list(self._by_id)}"
            )

    def for_agent(self, agent_name: str) -> List[AgenticPatternConfig]:
        """Return every pattern that lists *agent_name* among its agents.

        Matching is exact and case-sensitive against :pyattr:`AgentRef.name`,
        which should correspond to the agent's ``AgentCard.name``.

        Usage::

            from common.agentic_patterns import PATTERNS
            from agents.farms.brazil.card import AGENT_CARD

            my_patterns = PATTERNS.for_agent(AGENT_CARD.name)
        """
        return [p for p in self._by_id.values() if p.enabled and any(a.name == agent_name for a in p.agents)]

    def resolve(self, base_id: str) -> AgenticPatternConfig:
        """Find the enabled pattern variant whose id contains *base_id*.

        Useful when multiple transport-specific variants of the same
        logical pattern exist (e.g. ``slim-publish-subscribe`` and
        ``nats-publish-subscribe``).  Only the one marked ``enabled: true``
        in the YAML is returned::

            pattern = PATTERNS.resolve("publish-subscribe")
            # → whichever of slim-/nats- is enabled

        Args:
            base_id: Substring that must appear in the pattern id.

        Returns:
            The single enabled :class:`AgenticPatternConfig` matching
            *base_id*.

        Raises:
            KeyError: If no enabled pattern contains *base_id*, or if
                multiple enabled patterns match (ambiguous).
        """
        matches = [
            p for p in self._by_id.values()
            if p.enabled and base_id in p.id
        ]
        if not matches:
            raise KeyError(
                f"No enabled pattern matching {base_id!r}. "
                f"Available (enabled): {[p.id for p in self._by_id.values() if p.enabled]}"
            )
        if len(matches) > 1:
            raise KeyError(
                f"Ambiguous: multiple enabled patterns match {base_id!r}: "
                f"{[m.id for m in matches]}. Disable all but one or use get() with an exact id."
            )
        return matches[0]

    def list_all(self, omit_disabled: bool = True) -> List[AgenticPatternConfig]:
        if omit_disabled:
            return [p for p in self._by_id.values() if p.enabled]
        return list(self._by_id.values())

    def __contains__(self, pattern_id: str) -> bool:
        return pattern_id in self._by_id

    def __iter__(self):
        return iter(self._by_id.values())

    def __len__(self) -> int:
        return len(self._by_id)


# ──────────────────────────────────────────────
# Load patterns from YAML
# ──────────────────────────────────────────────

_PATTERNS_YAML = Path(__file__).parent.parent / "config" / "agentic_patterns.yaml"
PATTERNS = PatternRegistry.from_file(str(_PATTERNS_YAML))