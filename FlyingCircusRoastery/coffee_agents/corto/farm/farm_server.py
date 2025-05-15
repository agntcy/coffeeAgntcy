import click

from a2a.server import A2AServer
from a2a.server.request_handlers import DefaultA2ARequestHandler
from a2a.types import (AgentAuthentication, AgentCapabilities, AgentCard,
                       AgentSkill)

from agent_executor import FarmAgentExecutor


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=9999)
def main(host: str, port: int):
    skill = AgentSkill(
        id='coffee_farm',
        name='Coffee Farm Message',
        description='Handles and echoes coffee farm-related user input.',
        tags=['coffee', 'farm', 'echo', 'message'],
        examples=['plant arabica', 'status of coffee crops'],
    )

    agent_card = AgentCard(
        name='Coffee Farm Agent Server',
        description='An agent server that handles coffee farm-related messages and echoes user input.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
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
    main()