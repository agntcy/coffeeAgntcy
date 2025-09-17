# Copyright AGNTCY Contributors (https://github.com/agntcy)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express oqr implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import logging
from langgraph.graph import MessagesState
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from common.llm import get_llm

from agntcy_app_sdk.factory import AgntcyFactory
from ioa_observe.sdk.decorators import agent, graph

from config.config import (
    DEFAULT_MESSAGE_TRANSPORT,
    TRANSPORT_SERVER_ENDPOINT,
)

logger = logging.getLogger("lungo.colombia_farm_agent.agent")

# Initialize a multi-protocol, multi-transport agntcy factory.
factory = AgntcyFactory("lungo_colombia_farm", enable_tracing=True)

# --- 1. Define Node Names as Constants ---
class NodeStates:
    SUPERVISOR = "supervisor"
    INVENTORY = "inventory_node"
    ORDERS = "orders_node"
    ORDER_EVENT_TRACKER = "order_event_tracker"
    GENERAL_RESPONSE = "general_response_node"
    WEATHER_FORECAST = "weather_forecast_node"

# --- 2. Define the Graph State ---
class GraphState(MessagesState):
    """
    Represents the state of our graph, passed between nodes.
    """
    next_node: str

# --- 3. Implement the LangGraph Application Class ---
@agent(name="colombia_farm_agent")
class FarmAgent:
    def __init__(self):
        """
        Initializes the CustomerServiceAgent with an LLM and builds the LangGraph workflow.

        Args:
            llm_model (str): The name of the OpenAI LLM model to use (e.g., "gpt-4o", "gpt-3.5-turbo").
        """
        self.supervisor_llm = None
        self.inventory_llm = None
        self.orders_llm = None
        self.weather_forecast_llm = None

        self.app = self._build_graph()

    # --- Node Definitions ---

    def _supervisor_node(self, state: GraphState) -> dict:
        """
        Determines the intent of the user's message and routes to the appropriate node.
        """
        if not self.supervisor_llm:
            self.supervisor_llm = get_llm()

        prompt = PromptTemplate(
            template="""You are a coffee farm manager in Colombia who delegates farm cultivation and global sales. Based on the 
            user's message, determine if it's related to 'inventory', 'orders', or 'order_event_tracker'.
            Respond with 'inventory' if the message is about checking yield, stock, product availability, or specific coffee item details.
            Respond with 'orders' if the message is about checking order status, placing an order, or modifying an existing order.
            Respond with 'order_event_tracker' if the message content contains 'RECEIVED_ORDER'.
            If unsure, respond with 'general'.

            User message: {user_message}
            """,
            input_variables=["user_message"]
        )

        chain = prompt | self.supervisor_llm
        response = chain.invoke({"user_message": state["messages"]})
        intent = response.content.strip().lower()

        logger.info(f"Supervisor intent determined: {intent}")  # Log the intent for debugging

        if "inventory" in intent:
            # return {"next_node": NodeStates.INVENTORY, "messages": state["messages"]}
            return {"next_node": NodeStates.WEATHER_FORECAST, "messages": state["messages"]}
        elif "orders" in intent:
            return {"next_node": NodeStates.ORDERS, "messages": state["messages"]}
        elif "order_event_tracker" in intent:
            return {"next_node": NodeStates.ORDER_EVENT_TRACKER, "messages": state["messages"]}
        else:
            return {"next_node": NodeStates.GENERAL_RESPONSE, "messages": state["messages"]}
        
    async def _get_weather_forecast(self, state: GraphState) -> str:

        # extract location from latest user message
        if not self.weather_forecast_llm:
            self.weather_forecast_llm = get_llm()

        prompt = PromptTemplate(
            template="""You are a helpful assistant that parses user messages to extract location information.
            Based on the user's message, extract the location. Return a string with the location name.
            User message: {user_message}
            """,
            input_variables=["user_message"]
        )

        chain = prompt | self.weather_forecast_llm
        response = chain.invoke({"user_message": state["messages"]})
        location = response.content.strip().lower()

        logger.info(f"Weather location extracted: {location}")

        #return {"messages": [AIMessage(f"The weather forecast for {location} is: sunny and 75°F.")]}

        transport_instance = factory.create_transport(
            DEFAULT_MESSAGE_TRANSPORT, 
            endpoint=TRANSPORT_SERVER_ENDPOINT, 
            name="default/default/mcp_client")
        mcp_client = factory.create_client(
            "MCP",
            agent_topic="lungo_weather_service",
            transport=transport_instance,
        )

        # view available tools
        try:
            async with mcp_client as client:
                response = await client.list_tools()
                available_tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in response.tools
                ]
                logger.info(f"Available tools: {available_tools}")

                result = await client.call_tool(
                    name="get_forecast",
                    arguments={"location": location},
                )
                logger.info(f"Tool call result: {result}")

                mcp_call_result = ""
                if hasattr(result, "__aiter__"):
                    # gather streamed chunks
                    async for chunk in result:
                        delta = chunk.choices[0].delta
                        mcp_call_result += delta.content or ""
                else:
                    content_list = result.content
                    if isinstance(content_list, list) and len(content_list) > 0:
                        mcp_call_result = content_list[0].text
                    else:
                        mcp_call_result = "No content returned from tool."

                logger.info(f"Weather forecast result: {mcp_call_result}")
                logger.info(f"Weather forecast result as AIMeessage: {[AIMessage(mcp_call_result)]}")
                return {"messages": [AIMessage(mcp_call_result)]}
        except Exception as e:
            logger.error(f"Error during MCP tool call: {e}")
            return {"messages": [AIMessage(f"Error retrieving weather data: {str(e)}")]}
        finally:
            pass

    async def _inventory_node(self, state: GraphState) -> dict:
        """
        Handles inventory-related queries using an LLM to formulate responses.
        """
        if not self.inventory_llm:
            self.inventory_llm = get_llm()

        user_message = state["messages"]

        prompt = PromptTemplate(
            template="""You are a helpful Colombian coffee farm manager.
                You should estimate the seasonal coffee yield after checking the weather.
                Always return a numeric yield estimate with units (e.g. "5000 lbs").
                No explanation needed.

                User question: {user_message}
                """,
            input_variables=["user_message"]
        )
        chain = prompt | self.inventory_llm

        llm_response = chain.invoke({
            "user_message": user_message,
        }).content

        logger.info(f"Inventory response generated: {llm_response}")

        return {"messages": [AIMessage(llm_response)]}

    def _orders_node(self, state: GraphState) -> dict:
        """
        Handles order-related queries using an LLM to formulate responses.
        """
        if not self.orders_llm:
            self.orders_llm = get_llm()

        user_message = state["messages"]

        logger.info(f"Received order query: {user_message}")

        # Simulate data retrieval - in a real app, this would be a database/API call
        mock_order_data = {
            "12345": {"status": "processing", "estimated_delivery": "2 business days"},
            "67890": {"status": "shipped", "tracking_number": "ABCDEF123"}
        }

        prompt = PromptTemplate(
            template="""You are an order assistant. Based on the user's question and the following order data, provide a concise and helpful response.
            If they ask about a specific order number, provide its status. 
            If they ask about placing order an order, generate a random order id and tracking number.

            Order Data: {order_data}
            User question: {user_message}
            """,
            input_variables=["user_message", "order_data"]
        )
        chain = prompt | self.orders_llm

        llm_response = chain.invoke({
            "user_message": user_message,
            "order_data": str(mock_order_data) # Pass data as string for LLM context
        }).content

        return {"messages": [AIMessage(llm_response)]}

    def _order_event_tracker_node(self, state: GraphState) -> dict:
        """
        Handles order event tracking. If message content is 'RECEIVED_ORDER', responds with 'HANDOVER_TO_SHIPPER'.
        """
        user_message = state["messages"]
        
        # Extract the actual message content
        message_content = ""
        if isinstance(user_message, list) and len(user_message) > 0:
            message_content = user_message[0] if isinstance(user_message[0], str) else str(user_message[0])
        else:
            message_content = str(user_message)
        
        logger.info(f"Order event tracker checking message: {message_content}")
        
        if "RECEIVED_ORDER" in message_content:
            response = "HANDOVER_TO_SHIPPER"
            logger.info(f"Order event detected, responding with: {response}")
            return {"messages": [AIMessage(response)]}
        else:
            response = "No order event detected in message"
            logger.info(f"No order event detected: {response}")
            return {"messages": [AIMessage(response)]}

    def _general_response_node(self, state: GraphState) -> dict:
        """
        Provides a fallback response for unclear or out-of-scope messages.
        """
        response = "I'm designed to help with inventory and order-related questions. Could you please rephrase your request?"
        return {"messages": [AIMessage(response)]}

    # --- Graph Building Method ---

    @graph(name="colombia_farm_graph")
    def _build_graph(self):
        """
        Builds and compiles the LangGraph workflow.
        """
        workflow = StateGraph(GraphState)

        # Add nodes
        workflow.add_node(NodeStates.SUPERVISOR, self._supervisor_node)
        workflow.add_node(NodeStates.INVENTORY, self._inventory_node)
        workflow.add_node(NodeStates.ORDERS, self._orders_node)
        workflow.add_node(NodeStates.ORDER_EVENT_TRACKER, self._order_event_tracker_node)
        workflow.add_node(NodeStates.GENERAL_RESPONSE, self._general_response_node)
        workflow.add_node(NodeStates.WEATHER_FORECAST, self._get_weather_forecast)

        # Set the entry point
        workflow.set_entry_point(NodeStates.SUPERVISOR)

        # Add conditional edges from the supervisor
        workflow.add_conditional_edges(
            NodeStates.SUPERVISOR,
            lambda state: state["next_node"],
            {
                # NodeStates.INVENTORY: NodeStates.INVENTORY,
                NodeStates.ORDERS: NodeStates.ORDERS,
                NodeStates.ORDER_EVENT_TRACKER: NodeStates.ORDER_EVENT_TRACKER,
                NodeStates.GENERAL_RESPONSE: NodeStates.GENERAL_RESPONSE,
                NodeStates.WEATHER_FORECAST: NodeStates.WEATHER_FORECAST,
            },
        )

        # Add edges from the specific nodes to END
        workflow.add_edge(NodeStates.WEATHER_FORECAST, NodeStates.INVENTORY)
        workflow.add_edge(NodeStates.INVENTORY, END)
        workflow.add_edge(NodeStates.ORDERS, END)
        workflow.add_edge(NodeStates.ORDER_EVENT_TRACKER, END)
        workflow.add_edge(NodeStates.GENERAL_RESPONSE, END)

        return workflow.compile()

    # --- Public Methods for Interaction ---

    async def ainvoke(self, user_message: str) -> dict:
        """
        Invokes the graph with a user message.

        Args:
            user_message (str): The current message from the user.

        Returns:
            str: The final state of the graph after processing the message.
        """
        inputs = {"messages": [user_message]}
        result = await self.app.ainvoke(inputs)

        messages = result.get("messages", [])
        if not messages:
            raise RuntimeError("No messages found in the graph response.")

        # Find the last AIMessage with non-empty content
        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.content.strip():
                logger.debug(f"Valid AIMessage found: {message.content.strip()}")
                return message.content.strip()

        # If no valid AIMessage found, return the last message as a fallback
        return messages[-1].content.strip() if messages else "No valid response generated."

async def main():
    agent = FarmAgent() # You can specify llm_model='gpt-3.5-turbo' if you prefer
    print("--- Testing Order Event Tracker ---")
    messages = [
        "RECEIVED_ORDER",
        "We have RECEIVED_ORDER from customer 12345",
        "Something else happened",
    ]
    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await agent.ainvoke(msg)
        print(f"Agent: {final_state}")


# --- Example Usage ---
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())