# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Union, List, Optional, Dict
import uuid
from pydantic import BaseModel, Field
from enum import Enum
from a2a.types import AgentCard

class AgentProtocol(str, Enum):
    """The protocol used by the candidate agent."""

    A2A = "a2a"
    MCP = "mcp"


# Define the Union of all possible card types
CardType = Union[AgentCard]  # TODO: mcp currently has no defined Card type


class Candidate(BaseModel):
    """
    Represents a candidate agent with its associated protocol, card, and metadata.

    id: Unique identifier for the candidate.
    name: The name of the candidate agent.
    source_registry_url: The URL of the registry from which the candidate was sourced.
    agent_protocol: The protocol used by the candidate agent (A2A or MCP).
    card: The agent's card information.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str                
    source_registry_url: str
    agent_protocol: AgentProtocol
    agent_card: CardType


class Interview(BaseModel):
    """
    Represents an interview session with a candidate agent.
    """

    candidate_id: str
    evaluation_criteria: dict[str, str]  # TODO: More complex structure
    started_at: str | None = None  # ISO 8601 timestamp
    ended_at: str | None = None  # ISO 8601 timestamp
    transcript: list[str]  # TODO: More complex structure
    score: Optional[float] = None  # Evaluation score from Rogue AI
    passed: Optional[bool] = None  # Pass/fail status from evaluation
    rogue_job_id: Optional[str] = None  # Rogue AI evaluation job ID


class CandidatePool(BaseModel):
    """
    Represents a pool of candidate agents with ID-based mapping to interviews.
    """
    
    candidates: Dict[str, Candidate] = Field(default_factory=dict)
    interviews: Dict[str, Interview] = Field(default_factory=dict)
    ranks: Dict[str, float] = Field(default_factory=dict)
    
    def add_candidate_with_interview(self, candidate: Candidate, interview: Interview) -> str:
        """Add a candidate and their interview to the pool.
        
        Args:
            candidate: The candidate to add
            interview: The interview for the candidate
        
        Returns:
            The candidate ID
        """
        if interview.candidate_id != candidate.id:
            raise ValueError("Interview candidate_id must match candidate id")
        
        self.candidates[candidate.id] = candidate
        self.interviews[candidate.id] = interview
        return candidate.id