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
# and an async Client via the SDK
# Prerequisites: create a .env similar to .env.sample based on the Agent deployment output (Refer deploy_acp/README.md).
# Usage: python test_clients/acp_client/client_async.py

import asyncio
import json
import os

from agntcy_acp import ApiClientConfiguration, AsyncACPClient
from agntcy_acp.acp_v0.async_client.api_client import \
    ApiClient as AsyncApiClient
from agntcy_acp.models import Config, RunCreateStateless, RunError, RunResult
from dotenv import find_dotenv, load_dotenv
from httpx_sse import ServerSentEvent

from test_clients.acp_client.logging_config import configure_logging

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


async def run_stateless(query, process_event):
    """
  Create a stateless run with the input spec from jarvis-agent.json and stream the output.
  Calls process_event(event, user_email) for each streamed event.
  """
    # Host can't have trailing slash
    client_config = ApiClientConfiguration(
        host=f"http://localhost:{os.environ['API_PORT']}", api_key={"x-api-key": os.environ["API_KEY"]}, retries=3
    )

    async with AsyncApiClient(client_config) as api_client:

        acp_client = AsyncACPClient(api_client)
        agent_id = os.environ["AGENT_ID"]

        input_obj = {"messages": [{"type": "human", "content": query}], "is_completed": False}
        # Ensure all message types are valid
        for message in input_obj["messages"]:
            if message["type"] not in ["human", "assistant", "ai", "tool"]:
                raise ValueError(f"Invalid message type: {message['type']}")
        run_create = RunCreateStateless(
            agent_id=agent_id,
            input=input_obj,
            config=Config(),
        )
        # Create the stateless run and stream its output
        run_output = await acp_client.create_and_wait_for_stateless_run_output(run_create)
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
        # logging.info(run_state)
        if "messages" in run_state:
            for i, m in enumerate(run_state["messages"]):
                metadata = run_state.get("metadata", [{}] * len(run_state["messages"]))
                event = ServerSentEvent(
                    event="data", data=json.dumps({"answer": m["content"], "metadata": metadata[i]})
                )
                await process_event(query, event)  # run = await acp_client.create_stateless_run(run_create)


if __name__ == "__main__":
    load_environment_variables()

    async def process_event(query, event):
        print(f"Query:{query}, Event: {event.event}, Data: {event.data}")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_stateless("Need 100 tons of Arabica roast from Vietnam region by December 15", process_event))
