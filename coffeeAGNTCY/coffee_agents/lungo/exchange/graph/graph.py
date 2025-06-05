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

from langchain_core.messages import AIMessage

from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from common.llm import get_llm
from farms.brazil.card import AGENT_CARD as brazil_agent_card
from farms.colombia.card import AGENT_CARD as colombia_agent_card
from farms.vietnam.card import AGENT_CARD as vietnam_agent_card
from graph.tools import FetchBrazilHarvestTool, FetchcolombiaHarvestTool, FetchVietnamHarvestTool, GetFarmYieldTool

logger = logging.getLogger("corto.supervisor.graph")

class ExchangeGraph:
    def __init__(self):
        self.graph = self.build_graph()

    def build_graph(self) -> CompiledStateGraph:
        """
        Constructs and compiles a LangGraph instance.

        This function initializes a `SupervisorAgent` to create the base graph structure
        and uses an `InMemorySaver` as the checkpointer for the compilation process.

        The resulting compiled graph can be used to execute Supervisor workflow in LangGraph Studio.

        Returns:
        CompiledGraph: A fully compiled LangGraph instance ready for execution.
        """
        model = get_llm()

        get_farm_yields_tool = GetFarmYieldTool()

        get_farm_yields_tool = create_react_agent(
            model=model,
            tools=[get_farm_yields_tool],
            name="get_farm_yields",
        )
    
        fetch_brazil_harvest_tool = FetchBrazilHarvestTool(
            remote_agent_card=brazil_agent_card,
        )

        fetch_brazil_harvest = create_react_agent(
            model=model,
            tools=[fetch_brazil_harvest_tool],
            name="fetch_brazil_harvest",
        )
        fetch_colombia_harvest_tool = FetchcolombiaHarvestTool(
            remote_agent_card=colombia_agent_card,
        )

        fetch_colombia_harvest = create_react_agent(
            model=model,
            tools=[fetch_colombia_harvest_tool],
            name="fetch_colombia_harvest",
        )

        fetch_vietnam_harvest_tool = FetchVietnamHarvestTool(
            remote_agent_card=vietnam_agent_card,
        )
        fetch_vietnam_harvest = create_react_agent(
            model=model,
            tools=[fetch_vietnam_harvest_tool],
            name="fetch_vietnam_harvest",
        )
        graph = create_supervisor(
            model=model,
            agents=[get_farm_yields_tool, fetch_brazil_harvest, fetch_colombia_harvest, fetch_vietnam_harvest],  # worker agents list
            prompt = (
            "You are a supervisor agent responsible for handling coffee requests in pounds (lb).\n\n"

            "## TASK FLOW:\n"
            "1. Use the tool `get_farm_yields` to retrieve a dictionary mapping farm names to their available coffee yields in pounds.\n"
            "2. Use only the exact keys returned by `get_farm_yields`. Do **not** make up or assume any farm names.\n"
            "3. Select the farm with the highest available yield that meets or exceeds the request. Do not ask the user to choose. Always proceed automatically with the top-yielding valid farm.\n"
            "   - If no single farm has enough yield, respond accordingly (see rules below).\n"
            "4. Based on the selected farm, call the corresponding harvest tool. Each farm will have a tool named `fetch_<lowercased_farmname>_harvest`.\n"
            "   - Input: a dictionary with keys `farm` (string) and `amount` (int)\n\n"

            "## RULES:\n"
            "- Only continue if the user clearly requests coffee in a type of weight or number. If no weight type is given, assume pounds. Accept common typos like 'lbs', 'pouds', 'punds'.\n"
            "- If the weight is given in another unit (e.g., kg), convert it to pounds.\n"
            "- If the request does **not** mention coffee or a quantity, respond with:\n"
            "  \"I'm sorry, I can only help with requests to obtain coffee beans. Please specify the amount you need.\"\n"
            "- **Do not combine yields from multiple farms**. Only use one farm that can fully satisfy the request.\n"
            "- If **no single farm** can fulfill the request, respond with:\n"
            "  \"I'm sorry, but none of the farms can fulfill your request for coffee beans.\"\n"
            "- If `get_farm_yields` fails or returns no farms, provide a user-friendly error.\n"
            "- If the selected farm tool fails, return a clear error message.\n"
            "- If all steps succeed, reply in this format:\n"
            "  \"{FarmName} will fulfill your order of {X} lb of coffee. It will be sent to you shortly.\"\n"
        ),
            # add_handoff_back_messages=False,
            output_mode="last_message",
        ).compile()
        logger.debug("LangGraph supervisor created and compiled successfully.")
        return graph

    async def serve(self, prompt: str):
        """
        Processes the input prompt and returns a response from the graph.
        Args:
            prompt (str): The input prompt to be processed by the graph.
        Returns:
            str: The response generated by the graph based on the input prompt.
        """
        try:
            logger.debug(f"Received prompt: {prompt}")
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("Prompt must be a non-empty string.")
            result = await self.graph.ainvoke({
                "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
                ],
            }, {"configurable": {"thread_id": uuid.uuid4()}})

            logger.debug(f"Graph response: {result}")
            messages = result.get("messages", [])
            logger.debug(f"Graph response messages: {messages}")
            if not messages:
                raise RuntimeError("No messages found in the graph response.")

            # Find the last AIMessage with non-empty content
            for message in reversed(messages):
                if isinstance(message, AIMessage) and message.content.strip():
                    logger.debug(f"Valid AIMessage found: {message.content.strip()}")
                    return message.content.strip()

            raise RuntimeError("No valid AIMessage found in the graph response.")
        except ValueError as ve:
            logger.error(f"ValueError in serve method: {ve}")
            raise ValueError(str(ve))
        except Exception as e:
            logger.error(f"Error in serve method: {e}")
            raise Exception(str(e))
