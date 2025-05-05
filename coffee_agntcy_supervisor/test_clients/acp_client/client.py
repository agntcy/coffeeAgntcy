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

# Description: This is an example client demonstrating -
# ACP request for a stateless run using SDK function-create_and_wait_for_stateless_run_output
# and a sync Client via the SDK
# Prerequisites: create a .env similar to .env.sample based on the Agent deployment output (Refer deploy_acp/README.md).
# Usage: python clients/acp_client/client.py

import json
import logging
import os
import traceback
from typing import Annotated, Any, Dict, List, TypedDict

from agntcy_acp import ACPClient, ApiClientConfiguration
from agntcy_acp.acp_v0.sync_client.api_client import ApiClient
from agntcy_acp.models import Config, RunCreateStateless, RunError, RunResult
from dotenv import find_dotenv, load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from logging_config import configure_logging

logger = configure_logging()


def load_environment_variables(env_file: str | None = None) -> None:
    """
    Load environment variables from a .env file safely.

    This function loads environment variables from a `.env` file, ensuring
    that critical configurations are set before the application starts.

    Args:
        env_file (str | None): Path to a specific `.env` file. If None,
                               it searches for a `.env` file automatically.

    Behavior:
    - If `env_file` is provided, it loads the specified file.
    - If `env_file` is not provided, it attempts to locate a `.env` file in the project directory.
    - Logs a warning if no `.env` file is found.

    Returns:
        None
    """
    env_path = env_file or find_dotenv()

    if env_path:
        load_dotenv(env_path, override=True)
        logger.info(f".env file loaded from {env_path}")
    else:
        logger.warning("No .env file found. Ensure environment variables are set.")


# Define the graph state
class GraphState(TypedDict):
    """Represents the state of the graph, containing a list of messages."""
    messages: Annotated[List[BaseMessage], add_messages]


def node_remote_request_stateless(state: GraphState) -> Dict[str, Any]:
    """
    Create a stateless run with the input spec from acorda_agent.json and get the output.

    Args:
        state (GraphState): The current graph state containing messages.

    Returns:
        Dict[str, List[BaseMessage]]: Updated state containing server response or error message.
    """
    if not state["messages"]:
        logger.error(json.dumps({"error": "GraphState contains no messages"}))
        return {"messages": [HumanMessage(content="Error: No messages in state")]}

    query = state["messages"][-1].content
    logger.info(json.dumps({"event": "sending_request", "query": query}))

    # Host can't have trailing slash
    client_config = ApiClientConfiguration(
        host=f"http://localhost:{os.environ['API_PORT']}", api_key={"x-api-key": os.environ["API_KEY"]}, retries=3
    )

    with ApiClient(configuration=client_config) as api_client:
        acp_client = ACPClient(api_client)
        agent_id = os.environ["AGENT_ID"]
        input_obj = {"messages": [{"type": "human", "content": query}], "is_completed": False}
        run_create = RunCreateStateless(
            agent_id=agent_id,
            input=input_obj,
            config=Config(),
        )
        try:
            run_output = acp_client.create_and_wait_for_stateless_run_output(run_create)
            if run_output.output is None:
                raise Exception("Run output is None")
            actual_output = run_output.output.actual_instance
            if isinstance(actual_output, RunResult):
                run_result: RunResult = actual_output
            elif isinstance(actual_output, RunError):
                run_error: RunError = actual_output
                raise Exception(f"Run Failed: {run_error}")
            else:
                raise Exception(f"ACP Server returned a unsupported response: {run_output}")
            run_state = run_result.values  # type: ignore
            logging.info(f"run_state:{run_state}")
            if "messages" in run_state:
                for i, m in enumerate(run_state["messages"]):
                    msg = m["content"]
                    logging.info(f"{msg}")
            return {"messages": [AIMessage(content=json.dumps(msg))]}
        except Exception as e:
            error_msg = "Unexpected failure"
            logger.error(
                json.dumps(
                    {
                        "error": error_msg,
                        "exception": str(e),
                        "stack_trace": traceback.format_exc(),
                    }
                )
            )

    return {"messages": [HumanMessage(content=json.dumps(error_msg))]}


def build_graph() -> Any:
    """
    Constructs the state graph for handling request with the Remote Graph Server.

    Returns:
        StateGraph: A compiled LangGraph state graph.
    """
    builder = StateGraph(GraphState)
    builder.add_node("node_remote_request_stateless", node_remote_request_stateless)
    builder.add_edge(START, "node_remote_request_stateless")
    builder.add_edge("node_remote_request_stateless", END)
    return builder.compile()


def main():
    load_environment_variables()
    graph = build_graph()

    logger.info({"event": "invoking_graph", "input": input})
    user_prompt = "please provide details for project APT"
    # user_prompt = "UPDATE THIS PROMPT BASED ON PROMPTS IN clients/sample_prompts"
    inputs = {"messages": [HumanMessage(content=user_prompt)]}
    result = graph.invoke(inputs)
    logger.info({"event": "final_result", "result": result})


if __name__ == "__main__":
    main()
