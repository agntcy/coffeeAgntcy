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

import logging
import uuid
import json
from typing import List, Optional, Dict, Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import BaseTool, tool
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from common.llm import get_llm
from graph.tools import FlavorProfileTool
from exchange.models import Action
from farm.card import AGENT_CARD as farm_agent_card

logger = logging.getLogger("corto.supervisor.graph")


class DynamicTool(BaseTool):
    """Dynamically created tool from a CopilotKit Action"""

    action: Action = None
    schema: Dict = None

    def __init__(self, action: Action):
        schema = json.loads(action.jsonSchema)
        logger.info(f"Tool schema for {action.name}: {schema}")
        super().__init__(
            name=action.name,
            description=action.description,
            args_schema=schema,  # Use full schema instead of just properties
            return_direct=False,
        )
        self.action = action
        self.schema = schema

    def _run(self, **kwargs):
        """Execute the tool and return its result."""
        logger.info(f"DynamicTool {self.name} executing with args: {kwargs}")
        tool_result = json.dumps(kwargs)  # Return raw args as JSON for tool message
        logger.info(f"DynamicTool {self.name} produced result: {tool_result}")
        return tool_result

    def _return_direct(self) -> bool:
        logger.info(f"Checking return_direct for {self.name}")
        return False

    async def _arun(self, **kwargs):
        return self._run(**kwargs)


class ExchangeGraph:
    def __init__(self):
        self.base_tools = []
        self.graph = None

    def convert_actions_to_tools(self, actions: List[Action]) -> List[BaseTool]:
        """Convert Action objects to LangChain tools"""
        if not actions:
            logger.info("No actions to convert to tools")
            return []
        logger.info(
            f"Converting {len(actions)} actions to tools: {[a.name for a in actions]}"
        )
        tools = [DynamicTool(action) for action in actions]
        logger.info(f"Created tools: {[t.name for t in tools]}")
        return tools

    def build_graph(
        self, additional_tools: Optional[List[BaseTool]] = None
    ) -> CompiledStateGraph:
        """
        Constructs and compiles a LangGraph instance.

        This function initializes a `SupervisorAgent` to create the base graph structure
        and uses an `InMemorySaver` as the checkpointer for the compilation process.

        The resulting compiled graph can be used to execute Supervisor workflow in LangGraph Studio.

        Returns:
        CompiledGraph: A fully compiled LangGraph instance ready for execution.
        """
        model = get_llm()

        # Initialize base tools
        self.base_tools = [FlavorProfileTool(remote_agent_card=farm_agent_card)]

        # Combine base tools with additional tools if provided
        tools = self.base_tools + (additional_tools or [])
        logger.info(f"Total tools available to agent: {[t.name for t in tools]}")

        get_flavor_profile_a2a_agent = create_react_agent(
            model=model,
            tools=tools,  # list of tools for the agent
            name="get_flavor_profile_via_a2a",
        )
        graph = create_supervisor(
            model=model,
            agents=[get_flavor_profile_a2a_agent],  # worker agents list
            prompt=(
                "You are a supervisor agent.\n"
                "If the user's prompt is related to the flavor, taste, or sensory profile of coffee, assign the task to get_flavor_profile_via_a2a.\n"
                "If the prompt does not match any worker agent, respond kindly: "
                '"I\'m sorry, I cannot assist with that request. Please ask about coffee flavor or taste."\n'
                "If the worker agent returns control to you and it is a success and does not contain errors, do not generate any further messages or responses. End the conversation immediately by returning an empty response."
                "If the worker agent returns control to you and it is an error, give the same kind error message.\n"
            ),
            add_handoff_back_messages=False,
            output_mode="full_history",
        ).compile()
        logger.debug("LangGraph supervisor created and compiled successfully.")
        return graph

    async def serve(self, prompt: str, actions: List[Action] = None):
        """
        Processes the input prompt and returns a response from the graph.
        Args:
            prompt (str): The input prompt to be processed by the graph.
            actions (List[Action], optional): A list of Action objects that can be converted to tools.
        Returns:
            str: The response generated by the graph based on the input prompt.
        """
        try:
            logger.debug(f"Received prompt: {prompt}")
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("Prompt must be a non-empty string.")

            # Convert actions to tools and rebuild graph if needed
            additional_tools = (
                self.convert_actions_to_tools(actions) if actions else None
            )
            if additional_tools or self.graph is None:
                self.graph = self.build_graph(additional_tools)

            # Create initial messages state with proper message sequence
            initial_state = {
                "messages": [HumanMessage(content=prompt, id=str(uuid.uuid4())).dict()]
            }

            # Invoke the graph with proper configuration for message handling
            result = await self.graph.ainvoke(
                initial_state,
                {
                    "configurable": {
                        "thread_id": str(uuid.uuid4()),
                    },
                    "metadata": {
                        "copilotkit:emit-messages": True,
                        "copilotkit:emit-tool-calls": True,
                    },
                },
            )

            # Get and validate messages
            messages = result.get("messages", [])
            logger.info(f"Raw messages from graph: {messages}")
            if not messages:
                raise RuntimeError("No messages found in the graph response.")

            from .copilotkit_utils import langchain_to_copilotkit

            logger.info(f"Converting messages to copilotkit format...")

            copilotkit_messages = langchain_to_copilotkit(messages)
            logger.info(f"Converted to copilotkit messages: {copilotkit_messages}")
            return copilotkit_messages
        except ValueError as ve:
            logger.error(f"ValueError in serve method: {ve}")
            raise ValueError(str(ve))
        except Exception as e:
            logger.error(f"Error in serve method: {e}")
            raise Exception(str(e))
