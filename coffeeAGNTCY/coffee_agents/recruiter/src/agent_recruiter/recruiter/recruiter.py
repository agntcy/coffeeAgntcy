# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional
import os
from agent_recruiter.common.logging import get_logger

from agent_recruiter.models.recruiter_models import (
    RecruitmentRequest, 
    RecruitmentCriteria,
    SearchStrategy, 
    CandidatePool
)

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from agent_recruiter.common.llm import configure_llm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agent_recruiter.common.agent_utils import call_agent_async

from agent_recruiter.agent_registries import create_registry_search_agent
from agent_recruiter.interviewers import create_evaluation_agent

logger = get_logger("recruiter.recruiter")

configure_llm()

# ============================================================================
# Recruiter Agent Configuration
# ============================================================================

session_service = InMemorySessionService()

async def get_or_create_session(
    app_name: str, 
    user_id: str, 
    session_id: str
):
    """Retrieve an existing session or create a new one.

    This prevents AlreadyExistsError on repeated agent invocations.
    """

    session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if session is not None:
        logger.info(f"✅ Retrieved existing session '{session_id}' for user '{user_id}'.")
        return session
    
    # Define initial state data
    initial_state = {
        "user_preference_agent_registry": "AGNTCY Directory Service",
        "found_agent_records": {},  # Initialize empty dict for agent records from searches
    }

    session_stateful = await session_service.create_session(
        app_name=app_name, # Use the consistent app name
        user_id=user_id,
        session_id=session_id,
        state=initial_state # <<< Initialize state during creation
    )

    logger.info(f"✅ Session '{session_id}' created for user '{user_id}'.")

    # Verify the initial state was set correctly
    retrieved_session = await session_service.get_session(app_name=app_name,
            user_id=user_id,
            session_id = session_id)
    
    assert retrieved_session is not None, "Session retrieval failed."
    return session_stateful

# ============================================================================
# Agent Execution Functions
# ============================================================================

AGENT_INSTRUCTION = """You are the main Recruiter Agent coordinating a team.

You have specialized sub-agents:
- registry_search_agent: Finds agents in registries and directories based on user queries.
- agent_evaluator: Runs agentic interviews and evaluations on agents based on user-defined scenarios.

How to handle requests:
- If the user asks to find or search for agents or skills: delegate to the registry_search_agent
- If the user asks to EVALUATE, INTERVIEW, or assess agents: delegate to the agent_evaluator
- For anything else: respond appropriately or state you cannot handle it
"""

def create_recruiter_agent(sub_agents) -> Agent:
    """Create and configure the Recruiter Agent."""

    LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o")
    agent_team = Agent(
        name="RecruiterAgent",
        model=LiteLlm(model=LLM_MODEL),
        description="The main coordinator agent. Handles recruiter tasks and delegates specialized queries to sub-agents.",
        instruction=AGENT_INSTRUCTION,
        sub_agents=sub_agents,
    )

    return agent_team

class RecruiterTeam:
    """"""
    def __init__(self, app_name: str="agent_recruiter"):
        """Create necessary agents and runner."""
        self.app_name = app_name

        # 1. Create sub-agents
        registry_search_agent = create_registry_search_agent()
        evaluation_agent = create_evaluation_agent()
        sub_agents = [registry_search_agent, evaluation_agent]

        # 2. Create the root recruiter agent with sub-agents
        root_agent_stateful = create_recruiter_agent(sub_agents)
        self.root_agent = root_agent_stateful

        # 3. Create Runner with stateful session service
        runner_root_stateful = Runner(
            agent=root_agent_stateful,
            app_name=self.app_name,
            session_service=session_service
        )

        self.runner = runner_root_stateful

    def get_root_agent(self) -> Agent:
        """Get the root recruiter agent."""
        return self.root_agent

    async def get_found_agent_records(self, user_id: str, session_id: str) -> dict[str, dict]:
        """Retrieve agent records stored in session state by the registry search agent.

        Args:
            user_id: User ID for the session
            session_id: Session ID to retrieve state from

        Returns:
            Dict of agent records keyed by CID, or empty dict if none found
        """
        session = await session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        if session is None:
            logger.warning(f"Session '{session_id}' not found for user '{user_id}'")
            return {}

        return session.state.get("found_agent_records", {})

    async def clear_found_agent_records(self, user_id: str, session_id: str) -> bool:
        """Clear the found agent records from session state.

        Args:
            user_id: User ID for the session
            session_id: Session ID to clear state from

        Returns:
            True if cleared successfully, False if session not found
        """
        session = await session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        if session is None:
            logger.warning(f"Session '{session_id}' not found for user '{user_id}'")
            return False

        session.state["found_agent_records"] = {}
        logger.info(f"Cleared found agent records for session '{session_id}'")
        return True

    async def invoke(self, user_message: str, user_id: str, session_id: str) -> str:
        """Process a user message and return the agent response."""

        await get_or_create_session(app_name=self.app_name, user_id=user_id, session_id=session_id)

        response = await call_agent_async(user_message, self.runner, user_id, session_id)

        if not response.strip():
            raise RuntimeError("No valid response generated.")
        return response.strip()
    
async def main():
    recruiter_team = RecruiterTeam()

    print("--- Testing Recruiter Agent ---")
    messages = [
        # "What skills can I base searches on?",
        "Can you find an agent called Accountant agent?",
    ]
    user_id = "user_1"
    session_id = "recruiter_session"

    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await recruiter_team.invoke(msg, user_id, session_id)
        print(f"Agent: {final_state}")

    # Retrieve found agent records
    records = await recruiter_team.get_found_agent_records(user_id, session_id)
    print(f"\nFound {len(records)} agent records in session state:")
    for record in records:
        print(record)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


'''class AgentRecruiter:
    """
    An Agent Recruiter that can recruit agents from multiple registries, interview them, and select the best candidate.
    Features to consider implementing:

    - we want to recruiter based on skills, names, semantic search, etc.
    - we should have some type of semantic search to find agents based on skills and tasks.
    - we should cache interviews and results to avoid re-interviewing the same agents multiple times.
    - we should have a no-interview mode for trusted agents.
    """

    def __init__(self):
        self._registry: AgentRegistryBase = None
        self._interviewer: Optional[BaseInterviewer] = None

    def set_registry(self, registry: AgentRegistryBase):
        """Add a new agent registry to recruit from."""
        self._registries.append(registry)

    def set_interviewer(self, interviewer: BaseInterviewer):
        """Set the interviewer to use for evaluating candidates."""
        self._interviewer = interviewer

    def _merge_search_results(
        self,
        results_by_criteria: dict[str, List],
        strategy: SearchStrategy,
        max_candidates: int,
    ) -> List:
        """
        Merge search results from multiple criteria based on the search strategy.

        Args:
            results_by_criteria: Dict mapping criteria key to list of agent results
            strategy: How to combine results (INTERSECTION, UNION, RANKED)
            max_candidates: Maximum number of agents to return

        Returns:
            List of merged agent results
        """
        return []
    
    async def find_agents_by_prompt(self, prompt: str, max_candidates: int = 10) -> List:
        """Find agents based on a natural language prompt."""

        llm = get_llm()
        
        # convert prompt to recruitment criteria
        request = RecruitmentCriteria.from_prompt(prompt, llm=llm)
        if request is None:
            raise ValueError("Could not parse recruitment criteria from prompt")

        return await self.find_agents_by_search_criteria(request, max_candidates=max_candidates)

    async def find_agents_by_search_criteria(self, query: RecruitmentCriteria, max_candidates: int = 10) -> List:
        """Find agents based on the recruitment criteria."""
    
        criteria = request.criteria
        
        results_by_criteria: dict[str, List] = {}

        for registry in self._registries:
            registry_name = registry.registry_metadata().name
            logger.info(f"Searching in registry: {registry_name}")

            # 1. Exact name match
            if criteria.name:
                key = f"{registry_name}:name"
                result = registry.search_agents_by_name(criteria.name, limit=max_candidates)
                if result is not None:
                    results_by_criteria[key] = result if isinstance(result, list) else [result]

            # 2. Skills-based search
            for skill in criteria.skills:
                key = f"{registry_name}:skill:{skill}"
                result = registry.search_agents_by_skill(skill, limit=max_candidates)
                if result:
                    results_by_criteria[key] = result

            # 3. Semantic query (TODO: implement in registry)
            if criteria.semantic_query:
                logger.warning("Semantic query search not yet implemented")

        merged = self._merge_search_results(
            results_by_criteria,
            criteria.search_strategy,
            max_candidates,
        )
        logger.info(f"Total agents found after merge: {len(merged)}")
        return merged

    async def recruit_agents(self, request: RecruitmentRequest) -> CandidatePool:
        """Recruit agents based on the given criteria."""

        logger.info("Starting agent recruitment process.")
        # start with list of candidates from registries

        cards = []
        for registry in self._registries:
            if request.criteria.name is not None:


                agent_data = registry.search_agents_by_name(request.criteria.name)

                card_data = registry.extract_protocol_card_from_record(agent_data)
                if card_data is not None:
                    logger.info(f"Extracted card data for agent '{card_data.name}' from registry '{registry.registry_metadata().name}'")
                    cards.append(card_data)

            logger.info(f"Found {len(cards)} cards in registry: {registry.registry_metadata().name}")


        conduct_intervews = input(
            f"About to conduct interviews with {len(cards)} candidates. Proceed? (y/n): "
        )

        resp = await self._interviewer.conduct_interview(cards[0])
        return resp

        #return CandidatePool(candidates=[])'''