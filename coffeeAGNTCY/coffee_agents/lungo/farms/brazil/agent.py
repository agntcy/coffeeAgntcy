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
from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from enum import Enum
from sys import intern

from langgraph.graph import END, START, StateGraph
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage

from common.llm import get_llm

logger = logging.getLogger("longo.colombia_farm_agent.agent")

### Graph States
class GraphState(Enum):
  YIELD_ESTIMATE = intern("yield_estimate")
  FULLFILL_ORDER = intern("fullfill_order")

### Router Next Actions
RouterNextActions = Literal[
  GraphState.YIELD_ESTIMATE.value,
  GraphState.FULLFILL_ORDER.value
]

class SupervisorAction(BaseModel):
  action: RouterNextActions = Field(description="The action you will take to service the user") # type: ignore

# Agent Node Names
SUPERVISOR_AGENT = intern("supervisor_agent")
YIELD_AGENT = intern("yield_agent")
ORDERS_AGENT = intern("orders_agent")

class State(MessagesState):
    next: Literal[
        GraphState.YIELD_ESTIMATE,
        GraphState.FULLFILL_ORDER
    ]

    prompt: str
    error_type: str
    error_message: str
    yield_estimate: str
    order_details: str

class FarmAgent:
    def __init__(self):
        graph_builder = StateGraph(State)

        # add node states
        graph_builder.add_node(SUPERVISOR_AGENT, self.supervisor_node)
        graph_builder.add_node(YIELD_AGENT, self.yield_node)
        graph_builder.add_node(ORDERS_AGENT, self.orders_node)

        # add edge transitions
        graph_builder.add_edge(START, SUPERVISOR_AGENT)
        graph_builder.add_edge(YIELD_AGENT, END)
        graph_builder.add_edge(ORDERS_AGENT, END)
        self._agent = graph_builder.compile()

    # Supervisor Node
    async def supervisor_node(self, state: State):
        llm_supervisor = get_llm().with_structured_output(SupervisorAction, strict=True)
        sys_msg_supervisor = SystemMessage(
            content="""You are a coffee farm in Brazil.

            You can assist with the following operations:
            1. **Yield Estimate**: Provide a yield estimate for coffee beans based on user input.
            2. **Order Fulfillment**: Process orders related to coffee beans, including price and quantity.
            """,
            pretty_repr=True,
            )
        
        try:
            logger.info(f"Entering supervisor agent with state: {state}")
    
            response = await llm_supervisor.ainvoke(
                [sys_msg_supervisor, HumanMessage(content=state["prompt"])]
            )
            logging.info(f"got response from supervisor agent: {response}")

            return {"next": response.action, "prompt": state["prompt"]}
        except Exception as e:
            logging.error(f"Error during supervisor agent invoke: {e}")
            return {"next": "what can you do"} # TODO: add a fallback node state

    async def orders_node(self, state: State):
        """
        Facilitate the processing of orders related to coffee beans. 
        
        Args:
            state (State): The current state containing the user prompt with a price and quantity.  
        Returns:
            dict: A dictionary containing the order details or an error message if the input is invalid."""
        
        logger.info(f"Entering orders node with prompt: {state.get('prompt')}")
        
        # check for price and quantity in the prompt

        return {
            "messages": ["Order processed successfully. A shipment will be sent to you soon."]
        }

    async def yield_node(self, state: State):
        """
        Generate a yield estimate for coffee beans based on user input by connecting to an LLM.

        Args:
            state (State): The current state containing the user prompt.
        Returns:
            dict: A dictionary containing the yield estimate or an error message if the input is invalid.
        """
        logger.info(f"Entering yield node with prompt: {state.get('prompt')}")
        user_prompt = state.get("prompt")

        system_prompt = (
            "You are a coffee farm in Brazil\n"
            "The user will describe a question or scenario related to fetching the yield from your coffee farm. "
            "Your job is to:\n"
            "1. Return a random yield estimate for the coffee farm in Brazil. Make sure the estimate is a reasonable value and in pounds.\n"
            "2. Respond with only the yield estimate in pounds, without any additional text or explanation.\n"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = get_llm().invoke(messages)
        yield_estimate = response.content
        if not yield_estimate.strip():
            return {
                "error_type": "invalid_input",
                "error_message": "Invalid prompt. Please provide a valid question or scenario related to fetching the yield from the Brazilian coffee farm."
            }

        return {"yield_estimate": yield_estimate}

    async def ainvoke(self, input: str) -> dict:
        """
        Asynchronously invoke the agent with the given input.
        Args:
            input (str): The user input to process.
        Returns:
            dict: The result of the agent's processing, containing yield estimates or an error message.
        """
        resp = await self._agent.ainvoke({"prompt": input})

        print(f"Response from Brazil farm agent: {resp}")
    
        return resp
