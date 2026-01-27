# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Union, List, Optional, Any, Dict
import logging
import uuid
from pydantic import BaseModel, Field
from enum import Enum
from a2a.types import AgentCard
from langchain_openai import ChatOpenAI


class SearchStrategy(str, Enum):
    """Strategy for combining multiple search criteria."""

    INTERSECTION = "intersection"  # AND: agents must match all criteria
    UNION = "union"                # OR: agents matching any criteria
    RANKED = "ranked"              # Score agents by number of criteria matched


class AgentRecord(BaseModel):
    """Represents an agent record found in a registry search.

    This model is used to store structured agent records in session state
    so they can be accessed by other agents in the team.
    """

    cid: Optional[str] = Field(default=None, description="Content ID of the agent record")
    name: Optional[str] = Field(default=None, description="Name of the agent")
    description: Optional[str] = Field(default=None, description="Description of the agent")
    skills: List[str] = Field(default_factory=list, description="List of agent skills")
    modules: List[str] = Field(default_factory=list, description="List of agent modules")
    version: Optional[str] = Field(default=None, description="Version of the agent")
    url: Optional[str] = Field(default=None, description="URL endpoint of the agent")
    protocol: Optional[str] = Field(default=None, description="Protocol type (a2a, mcp, etc.)")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw data from the registry")

    @classmethod
    def from_search_result(cls, result: Dict[str, Any]) -> "AgentRecord":
        """Create an AgentRecord from a raw search result dictionary.

        Args:
            result: Raw dictionary from MCP search

        Returns:
            AgentRecord instance with populated fields
        """
        return cls(
            cid=result.get("cid"),
            name=result.get("name"),
            description=result.get("description"),
            skills=result.get("skills", []),
            modules=result.get("modules", []),
            version=result.get("version"),
            url=result.get("url"),
            protocol=result.get("protocol"),
            raw_data=result
        )


class EvalScenarioExtraction(BaseModel):
    """Evaluation scenario extraction for structured output."""
    
    scenario: str = Field(description="Description of the evaluation scenario")
    expected_outcome: Optional[str] = Field(default=None, description="Expected outcome for this scenario")


class RecruitmentExtractionResult(BaseModel):
    """Structured output model for LLM extraction of recruitment criteria."""
    
    is_recruitment_related: bool = Field(description="Whether the prompt is related to recruitment/hiring at all")
    extraction_confidence: str = Field(description="Level of extraction confidence: 'high', 'medium', 'low'")
    unmatched_reason: Optional[str] = Field(default=None, description="Reason if prompt is not recruitment-related")
    
    # All extraction fields are optional to support partial matches
    name: Optional[str] = Field(default=None, description="Descriptive name for recruitment criteria")
    skills: List[str] = Field(default_factory=list, description="List of required skills")
    semantic_query: Optional[str] = Field(default=None, description="Semantic search query")
    policies: List[str] = Field(default_factory=list, description="Enterprise policies or constraints")
    evaluation_criteria: List[EvalScenarioExtraction] = Field(default_factory=list, description="Evaluation scenarios")
    search_strategy: SearchStrategy = Field(default=SearchStrategy.INTERSECTION, description="Search strategy")


class EvalScenario(BaseModel):
    """Evaluation scenario definition."""

    scenario: str
    expected_outcome: Optional[str] = None


class RecruitmentCriteria(BaseModel):
    """Defines the criteria for recruiting agents."""

    name: str | None = None
    skills: List[str] = []
    semantic_query: str | None = None
    policies: List[str] = []  # enterprise policies?
    evaluation_criteria: List[EvalScenario] = []
    search_strategy: SearchStrategy = SearchStrategy.INTERSECTION

    @classmethod
    def from_prompt(cls, prompt: str, llm: ChatOpenAI) -> Optional["RecruitmentCriteria"]:
        """Populate criteria based on a natural language prompt
        
        Args:
            prompt: Natural language prompt describing recruitment criteria
            llm: LLM instance to use for extraction
            
        Returns:
            RecruitmentCriteria instance with populated fields (even partial), None only if completely unrelated to recruitment
        """
        logger = logging.getLogger(__name__)
        
        # Create structured LLM with output schema
        structured_llm = llm.with_structured_output(RecruitmentExtractionResult)
        
        # Define extraction prompt for the LLM
        extraction_prompt = f"""
You are tasked with extracting recruitment criteria from a natural language prompt. 
Analyze the following prompt and extract ANY information that could be related to hiring, recruiting, or selecting agents/people.

Prompt: "{prompt}"

IMPORTANT: Even if you can only extract ONE field reliably, that's valuable! Extract whatever you can:

- name: A descriptive name for this recruitment criteria
- skills: ANY skills, technologies, or capabilities mentioned (technical skills, soft skills, domain expertise, etc.)
- semantic_query: A search query that captures what's being looked for (can be very general)
- policies: Any constraints, requirements, or policies mentioned
- evaluation_criteria: Ways to test or evaluate candidates
- search_strategy: How to combine criteria (default to "intersection")

Set is_recruitment_related to:
- true: If the prompt has ANY connection to hiring, finding people, selecting agents, job requirements, etc.
- false: ONLY if the prompt is completely unrelated (e.g., weather, math problems, random chat)

Set extraction_confidence based on how much you could extract:
- 'high': Multiple clear fields extracted
- 'medium': Some fields extracted with reasonable confidence  
- 'low': Only minimal/uncertain extraction possible

Be generous with extraction - if someone mentions "Python developer" extract both skills=["Python"] and semantic_query="Python developer". If they say "find someone good with databases", extract skills=["databases"] even if vague.

Even partial information is valuable for recruitment!"""

        try:
            # Get structured response from LLM
            result: RecruitmentExtractionResult = structured_llm.invoke([{"role": "user", "content": extraction_prompt}])
            
            logger.debug(f"LLM extraction result: is_recruitment_related={result.is_recruitment_related}, confidence={result.extraction_confidence}, fields_extracted={bool(result.name or result.skills or result.semantic_query)}")
            
            # Only return None if completely unrelated to recruitment
            if not result.is_recruitment_related:
                logger.info(f"Prompt not related to recruitment: {result.unmatched_reason}")
                return None
            
            # Convert evaluation criteria to EvalScenario objects
            eval_criteria = [
                EvalScenario(
                    scenario=criteria.scenario,
                    expected_outcome=criteria.expected_outcome
                )
                for criteria in result.evaluation_criteria
            ]
            
            # Create RecruitmentCriteria even with partial data
            criteria = cls(
                name=result.name,
                skills=result.skills,
                semantic_query=result.semantic_query,
                policies=result.policies,
                evaluation_criteria=eval_criteria,
                search_strategy=result.search_strategy
            )
            
            logger.info(f"Successfully extracted recruitment criteria (confidence: {result.extraction_confidence}) - name: {bool(result.name)}, skills: {len(result.skills)}, semantic_query: {bool(result.semantic_query)}")
            return criteria
            
        except Exception as e:
            logger.error(f"Error extracting recruitment criteria from prompt: {str(e)}")
            return None


class RecruitmentRequest(BaseModel):
    """Defines a user-issued recruitment request."""

    criteria: RecruitmentCriteria
    pull_from_registries: List[str] = []  # Names of registries to pull candidates from
    max_candidates: int = 10
    interview_mode: bool = True
    deep_test_mode: bool = False
    interviewer_llm: Optional[str] = "openai/o4-mini"
    interviewer_llm_api_key: Optional[str] = None


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
    
    def add_candidates_with_interviews(self, candidates: List[Candidate], interviews: List[Interview]) -> List[str]:
        """Add multiple candidates and their interviews to the pool.
        
        Args:
            candidates: List of candidates to add
            interviews: List of interviews for the candidates
        
        Returns:
            List of candidate IDs
        """
        if len(candidates) != len(interviews):
            raise ValueError("Number of candidates and interviews must match")
        
        result_ids = []
        for candidate, interview in zip(candidates, interviews):
            result_ids.append(self.add_candidate_with_interview(candidate, interview))
        return result_ids
    
    def assign_relative_rank(self, llm: ChatOpenAI) -> None:
        """Calculate and assign relative ranks to all candidates in the pool.
        
        Args:
            llm: LLM instance to use for ranking
        
        Note:
            This is a stub function. Implementation will calculate ranks based on:
            - Candidate qualifications vs requirements
            - Interview performance
            - Skills matching
            - Other evaluation metrics
        """
        # TODO: Implement ranking algorithm
        # This should analyze candidates and assign relative ranks (0.0 to 10.0)
        # Example: self.ranks[candidate_id] = calculated_score
        pass
    
    def get_rank(self, candidate_id: str) -> Optional[float]:
        """Get a candidate's rank by ID."""
        return self.ranks.get(candidate_id)
    
    def set_rank(self, candidate_id: str, rank: float) -> bool:
        """Set a candidate's rank.
        
        Returns:
            True if candidate exists and rank was set, False otherwise
        """
        if candidate_id in self.candidates:
            self.ranks[candidate_id] = rank
            return True
        return False
    
    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """Get a candidate by ID."""
        return self.candidates.get(candidate_id)
    
    def get_interview(self, candidate_id: str) -> Optional[Interview]:
        """Get an interview by candidate ID."""
        return self.interviews.get(candidate_id)
    
    def get_candidate_with_interview(self, candidate_id: str) -> Optional[tuple[Candidate, Interview]]:
        """Get both candidate and interview by candidate ID.
        
        Returns:
            Tuple of (candidate, interview) or None if candidate not found
        """
        candidate = self.get_candidate(candidate_id)
        interview = self.get_interview(candidate_id)
        if candidate and interview:
            return (candidate, interview)
        return None
    
    def remove_candidate(self, candidate_id: str) -> bool:
        """Remove a candidate, their interview, and rank from the pool.
        
        Returns:
            True if candidate was removed, False if not found
        """
        if candidate_id in self.candidates:
            del self.candidates[candidate_id]
            del self.interviews[candidate_id]
            self.ranks.pop(candidate_id, None)  # Remove rank if it exists
            return True
        return False
    
    def list_candidate_ids(self) -> List[str]:
        """Get all candidate IDs in the pool."""
        return list(self.candidates.keys())
    
    def list_candidates(self) -> List[Candidate]:
        """Get all candidates in the pool."""
        return list(self.candidates.values())
    
    def list_interviews(self) -> List[Interview]:
        """Get all interviews in the pool."""
        return list(self.interviews.values())
    
    def get_ranked_candidates(self, descending: bool = True) -> List[tuple[str, Candidate, float]]:
        """Get candidates sorted by rank.
        
        Args:
            descending: If True, sort by highest rank first. If False, lowest rank first.
        
        Returns:
            List of tuples (candidate_id, candidate, rank) sorted by rank
        """
        ranked_items = []
        for candidate_id, candidate in self.candidates.items():
            rank = self.ranks.get(candidate_id)
            if rank is not None:
                ranked_items.append((candidate_id, candidate, rank))
        
        return sorted(ranked_items, key=lambda x: x[2], reverse=descending)
    
    def size(self) -> int:
        """Get the number of candidates in the pool."""
        return len(self.candidates)