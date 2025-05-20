import click

from a2a.server import A2AServer
from a2a.server.request_handlers import DefaultA2ARequestHandler
from a2a.types import (AgentAuthentication, AgentCapabilities, AgentCard,
                       AgentSkill)

from agent_executor import FarmAgentExecutor
from config.config import FARM_AGENT_HOST, FARM_AGENT_PORT

def main(host: str, port: int):
    """Run the A2A server with the Farm Agent."""
    skill = AgentSkill(
        id='estimate_flavor',
        name='Estimate Flavor Profile',
        description='Estimates the flavor profile of coffee beans based on growing season and farm location.',
        tags=['coffee', 'flavor', 'profile', 'season', 'location'],
        examples=[
            '{"season": "harvest", "location": "Antigua, Guatemala"}',
            '{"season": "wet", "location": "Tarrazú, Costa Rica"}',
            '{"season": "summer", "location": "Yirgacheffe, Ethiopia"}',
        ],
        inputSchema={
            "type": "object",
            "properties": {
                "season": {
                    "type": "string",
                    "description": "Current growing season (e.g. 'harvest', 'dry', 'wet', 'summer', etc.)"
                },
                "location": {
                    "type": "string",
                    "description": "Name of the coffee-growing region (e.g. 'Yirgacheffe', 'Huila', 'Tarrazú')"
                }
            },
            "required": ["season", "location"]
        },
    )


    agent_card = AgentCard(
        name='Coffee Farm Flavor Agent',
        id='flavor-profile-farm-agent',
        description='An AI agent that estimates the flavor profile of coffee beans using growing conditions like season and altitude.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        defaultInputModes=["application/json"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(),
        skills=[skill],
        authentication=AgentAuthentication(schemes=['public']),
    )

    request_handler = DefaultA2ARequestHandler(
        agent_executor=FarmAgentExecutor()
    )

    server = A2AServer(agent_card=agent_card, request_handler=request_handler)
    server.start(host=host, port=port)

if __name__ == '__main__':
    main(FARM_AGENT_HOST, FARM_AGENT_PORT)