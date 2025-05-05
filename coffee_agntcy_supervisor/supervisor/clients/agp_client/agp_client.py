# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import os
import uuid
from typing import Annotated, Any, Dict, List, TypedDict

from agp_api.agent.agent_container import AgentContainer
from agp_api.gateway.gateway_container import GatewayContainer
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.messages.utils import convert_to_openai_messages
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from logging_config import configure_logging

logger = configure_logging()


class Config:
    """Configuration class for AGP (Agent Gateway Protocol) client.
    This class manages configuration settings for the AGP system, containing container
    instances for gateway and agent management, as well as remote agent specification.
    Attributes:
        gateway_container (GatewayContainer): Container instance for gateway management
        agent_container (AgentContainer): Container instance for agent management
        remote_agent (str): Specification of remote agent, defaults to "server"
    """
    remote_agent = "database_security_agent"
    gateway_container = GatewayContainer()
    agent_container = AgentContainer(local_agent=remote_agent)


# Define the graph state
class GraphState(TypedDict):
    """
    Represents the state of the graph, containing a list of messages and a
    gateway holder.
    """

    messages: Annotated[List[BaseMessage], add_messages]


async def send_and_recv(payload: Dict[str, Any], remote_agent: str) -> Dict[str, Any]:
    """
    Sends a payload to a remote agent and receives a response through the gateway container.
        payload (Dict[str, Any]): The request payload to be sent to the remote agent
        remote_agent (str): The identifier of the remote agent to send the payload to
    Returns:
        Dict[str, Any]: A dictionary containing the 'messages' key with either:
            - The last message received from the remote agent if successful
            - An error message if the request failed, wrapped in a HumanMessage
    Raises:
        May raise exceptions from gateway container operations or JSON processing
    Note:
        The response is expected to be a JSON string that can be decoded into a dictionary
        containing either an 'error' field (for failures) or an 'output' field with 'messages'
    """

    await Config.gateway_container.publish_messsage(
        payload, agent_container=Config.agent_container, remote_agent=remote_agent
    )
    _, recv = await Config.gateway_container.gateway.receive()

    response_data = json.loads(recv.decode("utf8"))

    print(json.dumps(response_data, indent=2))

    # check for errors
    error_code = response_data.get("error")
    if error_code is not None:
        error_msg = {
            "error": "AGP request failed",
            "status_code": error_code,
            "exception": response_data.get("message"),
        }
        logger.error(json.dumps(error_msg))
        return {"messages": [HumanMessage(content=json.dumps(error_msg))]}

    # decode message
    output = response_data.get("output", {})
    messages = output.get("messages", [])
    logger.info(messages)

    # We only store in shared memory the last message from remote to avoid duplication
    return {"messages": [messages[-1]]}

async def node_remote_agp(state: GraphState) -> Dict[str, Any]:
    """
    Sends a stateless request to the Remote Graph Server.

    Args:
        state (GraphState): The current graph state containing messages.

    Returns:
        Command[Literal["exception_node", "end_node"]]: Command to transition to the next node.
    """
    if not state["messages"]:
        logger.error(json.dumps({"error": "GraphState contains no messages"}))
        return {"messages": [HumanMessage(content="Error: No messages in state")]}

    # Extract the latest user query
    query = state["messages"][-1].content
    logger.info(json.dumps({"event": "sending_request", "query": query}))

    messages = convert_to_openai_messages(state["messages"])

    print("messages", messages)
    # payload to send to remote server at /runs endpoint
    payload: Dict[str, Any] = {
        "agent_id": "remote_agent",
        "input": {"messages": messages},
        "model": "gpt-4o",
        "metadata": {"id": str(uuid.uuid4())},
        # Add the route field to emulate the REST API
        "route": "/api/v1/runs",
    }
    print("payload", payload)

    logger.info(json.dumps({"event": "sending_payload", "payload": payload}))

    res = await send_and_recv(payload, remote_agent=Config.remote_agent)
    return res


async def init_client_gateway_conn(remote_agent: str = "server") -> None:
    """Initialize connection to the gateway.
    Establishes connection to a gateway service running on localhost using retry mechanism.
    Returns:
        None
    Raises:
        ConnectionError: If unable to establish connection after retries.
        TimeoutError: If connection attempts exceed max duration.
    Notes:
        - Uses default endpoint http://127.0.0.1:46357
        - Insecure connection is enabled
        - Maximum retry duration is 10 seconds
        - Initial retry delay is 1 second
        - Targets remote agent named "server"
    """

    Config.gateway_container.set_config(
        endpoint=os.getenv("AGP_GATEWAY_URL", "http://127.0.0.1:46357"), insecure=True
    )

    # Call connect_with_retry
    _ = await Config.gateway_container.connect_with_retry(
        agent_container=Config.agent_container,
        max_duration=10,
        initial_delay=1,
        remote_agent=remote_agent,
    )


# Build the state graph
async def build_graph() -> Any:
    """
    Constructs the state graph for handling requests.

    Returns:
        StateGraph: A compiled LangGraph state graph.
    """
    await init_client_gateway_conn(remote_agent=Config.remote_agent)
    builder = StateGraph(GraphState)
    #builder.add_node("node_remote_agp", node_remote_agp) # TODO: Implement this
    builder.add_node("node_remote_agp", node_remote_agp_fake)
    builder.add_edge(START, "node_remote_agp")
    builder.add_edge("node_remote_agp", END)
    return builder.compile()


async def main():
    """
    Main function to load environment variables, initialize the gateway connection,
    build the state graph, and invoke it with sample inputs.
    """
    load_dotenv(override=True)
    graph = await build_graph()

    test_input = {"sql_query": "SELECT * from customers limit 2;"
        , "ip_address": "192.168.90.11"}

    inputs = {"messages": [HumanMessage(content=json.dumps(test_input))]}
    logger.info({"event": "invoking_graph", "inputs": inputs})
    result = await graph.ainvoke(inputs)
    logger.info({"event": "final_result", "result": result})


# Main execution
if __name__ == "__main__":
    asyncio.run(main())
