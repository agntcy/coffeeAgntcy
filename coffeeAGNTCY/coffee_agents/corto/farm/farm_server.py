import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.types import (AgentCapabilities, AgentCard,
                       AgentSkill)

from agent_executor import FarmAgentExecutor
from config.config import FARM_AGENT_HOST, FARM_AGENT_PORT

def main(host: str, port: int):
    """Run the A2A server with the Farm Agent."""
    skill = AgentSkill(
        id="estimate_flavor",
        name="Estimate Flavor Profile",
        description="Analyzes a natural language prompt and returns the expected flavor profile for a coffee-growing region and/or season.",
        tags=["coffee", "flavor", "farm"],
        examples=[
            "What flavors can I expect from coffee in Huila during harvest?",
            "Describe the taste of beans grown in Sidamo in the dry season",
            "How does Yirgacheffe coffee taste?"
        ]
    )   

    agent_card = AgentCard(
        name='Coffee Farm Flavor Agent',
        id='flavor-profile-farm-agent',
        description='An AI agent that estimates the flavor profile of coffee beans using growing conditions like season and altitude.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
        supportsAuthenticatedExtendedCard=False,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    uvicorn.run(server.build(), host=host, port=port)

if __name__ == '__main__':
    main(FARM_AGENT_HOST, FARM_AGENT_PORT)