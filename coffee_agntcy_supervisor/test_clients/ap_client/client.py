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

# Description: This file contains a sample graph clients that makes a stateless request using langgraph agent protocol
# to the Remote Graph Server.
# Usage: python test_clients/ap_client/client.py

import json
import logging
import traceback
import uuid
from typing import Annotated, Any, Dict, List, TypedDict

import requests
from dotenv import find_dotenv, load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from logging_config import configure_logging
from requests.exceptions import (ConnectionError, HTTPError, RequestException,
                                 Timeout)

logger = configure_logging()

# URL for the Remote Graph Server /runs endpoint
REMOTE_SERVER_URL = f"http://localhost:8125/api/v1/runs"
logging.info(f"Remote server URL: {REMOTE_SERVER_URL}")

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
    Sends a stateless request to the Remote Graph Server.

    Args:
        state (GraphState): The current graph state containing messages.

    Returns:
        Dict[str, List[BaseMessage]]: Updated state containing server response or error message.
    """
    if not state["messages"]:
        logger.error(json.dumps({"error": "GraphState contains no messages"}))
        return {"messages": [HumanMessage(content="Error: No messages in state")]}

    logger.info("state[messages][-1]:", state["messages"][-1])
    query = state["messages"][-1].content
    logger.info(json.dumps({"event": "sending_request", "query": query}))

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "agent_id": "remote_agent",
        "model": "gpt-4o",
        "metadata": {"id": str(uuid.uuid4())},
        "input": {"query": query},
    }
    logger.info(f"Sending request to remote server with payload: {payload}")

    # Use a session for efficiency
    with requests.Session() as session:
        try:
            response = session.post(REMOTE_SERVER_URL, headers=headers, json=payload)
            response.raise_for_status()  # Raises HTTPError for 4xx and 5xx

            # Parse response as JSON
            response_data = response.json()
            logger.info(f"decoding response: {response_data}")
            # Decode JSON response
            decoded_response = decode_response(response_data)
            logger.info(f"decoded response:{decoded_response}")
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

        return {
            "agent_id": agent_id,
            "messages": output,
            "model": model,
            "metadata": metadata,
        }
    except Exception as e:
        return {"error": f"Failed to decode response: {str(e)}"}

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
    # load_environment_variables()
    graph = build_graph()

    logger.info({"event": "invoking_graph", "input": input})
    user_prompt = "Need 100 tons of Arabica roast from Vietnam region by December 15"
    #user_prompt = "UPDATE THIS PROMPT BASED ON PROMPTS IN clients/sample_prompts"
    inputs = {"messages": [HumanMessage(content=user_prompt)]}
    result = graph.invoke(inputs)
    logger.info({"event": "final_result", "result": result})

if __name__ == "__main__":
    main()
