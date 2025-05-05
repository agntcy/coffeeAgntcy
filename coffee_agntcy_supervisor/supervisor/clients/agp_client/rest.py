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

import json
import traceback
import uuid
from typing import Annotated, Any, Dict, List, Optional, TypedDict

import requests
from dotenv import find_dotenv, load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.messages.utils import convert_to_openai_messages
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from logging_config import configure_logging
from pydantic import BaseModel
from requests.exceptions import (ConnectionError, HTTPError, RequestException,
                                 Timeout)

# Initialize logger
logger = configure_logging()

# URL for the Remote Graph Server /runs endpoint
REMOTE_SERVER_URL = "http://127.0.0.1:8123/api/v1/runs"


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


def decode_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decodes the JSON response from the remote server and extracts relevant information.

    Args:
        response_data (Dict[str, Any]): The JSON response from the server.

    Returns:
        Dict[str, Any]: A structured dictionary containing extracted response fields.
    """
    try:
        agent_id = response_data.get("agent_id", "Unknown")
        output = response_data.get("output", {})
        model = response_data.get("model", "Unknown")
        metadata = response_data.get("metadata", {})

        # Extract messages if present
        messages = output.get("messages")

        return {
            "agent_id": agent_id,
            "messages": messages,
            "model": model,
            "metadata": metadata,
        }
    except Exception as e:
        return {"error": f"Failed to decode response: {str(e)}"}


# Define the graph state
class GraphState(TypedDict):
    """Represents the state of the graph, containing a list of messages."""

    messages: Annotated[List[BaseMessage], add_messages]


# Graph node that makes a stateless request to the Remote Graph Server
def node_remote_request_stateless(state: GraphState) -> Dict[str, Any]:
    """
    Sends a stateless request to the Remote Graph Server.

    Args:
        state (GraphState): The current graph state containing messages.

    Returns:
        Dict[str, List[BaseMessage]]: Updated state containing server response or error message.
    """
    if not state["messages"]:
        logger.error(json.dumps({"error": "GraphState contains no messages"}))
        return {"messages": [HumanMessage(content="Error: No messages in state")]}

    # Extract the latest user query
    query = state["messages"][-1].content

    logger.info({"event": "sending_request", "query": json.loads(query)})

    # Request headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    messages = convert_to_openai_messages(state["messages"])

    # payload to send to autogen server at /runs endpoint
    payload = {
        "agent_id": "remote_agent",
        "input": {"messages": messages},
        "model": "gpt-4o",
        "metadata": {"id": str(uuid.uuid4())},
        "route": "/api/v1/runs"
    }

    logger.info({"event": "payload", "query": payload})

    # Use a session for efficiency
    session = requests.Session()

    try:
        response = session.post(
            REMOTE_SERVER_URL, headers=headers, json=payload, timeout=10
        )

        # Raise exception for HTTP errors
        response.raise_for_status()

        # Parse response as JSON
        response_data = response.json()
        # Decode JSON response
        decoded_response = decode_response(response_data)

        logger.info(decoded_response)

        return {"messages": decoded_response.get("messages", [])}

    except (Timeout, ConnectionError) as conn_err:
        error_msg = {
            "error": "Connection timeout or failure",
            "exception": str(conn_err),
        }
        logger.error(json.dumps(error_msg))
        return {"messages": [HumanMessage(content=json.dumps(error_msg))]}

    except HTTPError as http_err:
        error_msg = {
            "error": "HTTP request failed",
            "status_code": response.status_code,
            "exception": str(http_err),
        }
        logger.error(json.dumps(error_msg))
        return {"messages": [HumanMessage(content=json.dumps(error_msg))]}

    except RequestException as req_err:
        error_msg = {"error": "Request failed", "exception": str(req_err)}
        logger.error(json.dumps(error_msg))
        return {"messages": [HumanMessage(content=json.dumps(error_msg))]}

    except json.JSONDecodeError as json_err:
        error_msg = {"error": "Invalid JSON response", "exception": str(json_err)}
        logger.error(json.dumps(error_msg))
        return {"messages": [HumanMessage(content=json.dumps(error_msg))]}

    except Exception as e:
        error_msg = {
            "error": "Unexpected failure",
            "exception": str(e),
            "stack_trace": traceback.format_exc(),
        }
        logger.error(json.dumps(error_msg))

    finally:
        session.close()

    return {"messages": [AIMessage(content=json.dumps(error_msg))]}


# Build the state graph
def build_graph() -> Any:
    """
    Constructs the state graph for handling requests.

    Returns:
        StateGraph: A compiled LangGraph state graph.
    """
    builder = StateGraph(GraphState)
    builder.add_node("node_remote_request_stateless", node_remote_request_stateless)
    builder.add_edge(START, "node_remote_request_stateless")
    builder.add_edge("node_remote_request_stateless", END)
    return builder.compile()


# Main execution
if __name__ == "__main__":
    test_input = {"sql_query": "SELECT * from customers limit 2;"
        , "ip_address": "192.168.90.11"}

    graph = build_graph()

    inputs = {"messages": [HumanMessage(content=json.dumps(test_input))]}

    logger.info({"event": "invoking_graph", "inputs": test_input})
    result = graph.invoke(inputs)

    output = result["messages"][-1].content

    logger.info({"event": "final_result", "result": output})
