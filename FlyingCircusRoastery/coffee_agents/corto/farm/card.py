from a2a.types import (AgentAuthentication, AgentCapabilities, AgentCard,
                       AgentSkill)

AGENT_SKILL = AgentSkill(
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

AGENT_CARD = AgentCard(
    name='Coffee Farm Flavor Agent',
    id='flavor-profile-farm-agent',
    description='An AI agent that estimates the flavor profile of coffee beans using growing conditions like season and altitude.',
    url='',
    version='1.0.0',
    defaultInputModes=["application/json"],
    defaultOutputModes=["text/plain"],
    capabilities=AgentCapabilities(),
    skills=[AGENT_SKILL],
    authentication=AgentAuthentication(schemes=['public']),
)