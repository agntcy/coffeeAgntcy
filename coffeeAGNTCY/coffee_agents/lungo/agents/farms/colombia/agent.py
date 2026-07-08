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

from ioa_observe.sdk.decorators import agent, graph

from agents.exceptions import AuthError
from agents.farms.colombia.card import AGENT_CARD, AGENT_ID
from agents.mcp_servers.utils import invoke_payment_mcp_tool
from common.llm import get_llm
from common.mcp_client import call_mcp_tool

logger = logging.getLogger("lungo.colombia_farm_agent.agent")

# --- 1. Define Node Names as Constants ---
class NodeStates:
    SUPERVISOR = "supervisor"
    INVENTORY = "inventory_node"
    ORDERS = "orders_node"
    GENERAL_RESPONSE = "general_response_node"
    WEATHER_FORECAST = "weather_forecast_node"

# --- 2. Define the Graph State ---
class GraphState(MessagesState):
    """
    Represents the state of our graph, passed between nodes.
    """
    next_node: str
    weather_forecast_success: bool
    weather_forecast: str
    # Workflow identity propagated from the supervisor; used as an explicit
    # fallback for MCP event emission when OTel baggage is unavailable.
    workflow_name: str | None
    workflow_instance_id: str | None

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
            user's message, determine if it's related to 'inventory' or 'orders'.
            Respond with 'inventory' if the message is about checking yield, stock, product availability, or specific coffee item details.
            Respond with 'orders' if the message is about checking order status, placing an order, or modifying an existing order.
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
        else:
            return {"next_node": NodeStates.GENERAL_RESPONSE, "messages": state["messages"]}

    async def _get_weather_forecast(self, state: GraphState) -> dict:
        """
        Calls the "get_forecast" tool on the "lungo_weather_service" MCP server for a
        fixed location ("colombia") through the shared ``call_mcp_tool`` helper, which
        owns the agntcy-app-sdk client contract and result normalization (including
        streamed responses). Returns the forecast wrapped in an AIMessage under the
        "weather_forecast" key.

        If the MCP tool call fails, it logs the error and returns an error message
        similarly wrapped.

        Returns:
            dict: ``weather_forecast_success`` plus a single AIMessage holding the
                forecast string, or an error message if the call fails.
        """
        try:
            forecast = await call_mcp_tool(
                topic="lungo_weather_service",
                tool_name="get_forecast",
                arguments={"location": "colombia"},
                agent_id=AGENT_CARD.name,
                source=AGENT_ID,
                workflow_name=state.get("workflow_name"),
                instance_id=state.get("workflow_instance_id"),
                message_timeout=45,
                list_tools_first=True,
                extract_text=True,
            )
            logger.info(f"Weather forecast result: {forecast}")
            return {"weather_forecast_success": True, "weather_forecast": [AIMessage(forecast)]}
        except Exception as e:
            logger.error(f"Error during MCP tool call: {e}")
            return {"weather_forecast_success": False, "weather_forecast": [AIMessage("Weather Forecast MCP Server was Unavailable")]}

    async def _inventory_node(self, state: GraphState) -> dict:
        """
        Handles inventory-related queries using an LLM to formulate responses.
        """
        if not state["weather_forecast_success"]:
            err_msg = "Cannot estimate yield because Weather Forecast MCP Server was Unavailable."
            logger.warning(err_msg)
            return {"messages": [AIMessage(err_msg)]}

        if not self.inventory_llm:
            self.inventory_llm = get_llm()

        user_message = state["messages"][-1] if state.get("messages") else ""
        weather_forecast = state.get("weather_forecast", "")

        prompt = PromptTemplate(
            template="""You are a helpful Colombian coffee farm manager.
                You should estimate the seasonal coffee yield after checking the weather given.
                Always return a numeric yield estimate with units (e.g. "5000 lbs").
                This should contain the the basic yield for colombia (5000 lbs) plus an estimated bonus yield based on the weather forecast (e.g. + 100 lbs per temperature unit above 0).
                No explanation needed.

                Weather forecast: {weather_forecast}
                User question: {user_message}
                """,
            input_variables=["user_message", "weather_forecast"]
        )
        chain = prompt | self.inventory_llm

        llm_response = chain.invoke({
            "user_message": user_message,
            "weather_forecast": weather_forecast,
        }).content

        logger.info(f"Inventory response generated: {llm_response}")

        return {"messages": [AIMessage(llm_response)]}

    async def _orders_node(self, state: GraphState) -> dict:
        """
        Handles order-related queries using an LLM to formulate responses.
        """
        if not self.orders_llm:
            self.orders_llm = get_llm()

        user_message = state["messages"]

        logger.info(f"Received order query: {user_message}")

        workflow_name = state.get("workflow_name")
        workflow_instance_id = state.get("workflow_instance_id")

        # Call MCP tools before processing the order
        try:
            payment_result = await invoke_payment_mcp_tool(
                "create_payment", agent_id=AGENT_CARD.name, source=AGENT_ID,
                workflow_name=workflow_name, instance_id=workflow_instance_id,
            )
            logger.info(f"Payment result: {payment_result}")

            transactions_details = await invoke_payment_mcp_tool(
                "list_transactions", agent_id=AGENT_CARD.name, source=AGENT_ID,
                workflow_name=workflow_name, instance_id=workflow_instance_id,
            )
            logger.info(f"Transactions details: {transactions_details}")

        except AuthError as auth_err:
            return {"messages": [AIMessage(str(auth_err))]}

        except Exception as e:
            logger.error(f"Error during MCP tool calls: {e}")
            return {"messages": [AIMessage("Failed to process order due to MCP tool errors.")]}

        # Simulate data retrieval - in a real app, this would be a database/API call
        mock_order_data = {
            "12345": {"status": "processing", "estimated_delivery": "2 business days"},
            "67890": {"status": "shipped", "tracking_number": "ABCDEF123"}
        }

        logger.info(f"Mock order data: {mock_order_data}")

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
                NodeStates.GENERAL_RESPONSE: NodeStates.GENERAL_RESPONSE,
                NodeStates.WEATHER_FORECAST: NodeStates.WEATHER_FORECAST,
            },
        )

        # Add edges from the specific nodes to END
        workflow.add_edge(NodeStates.WEATHER_FORECAST, NodeStates.INVENTORY)
        workflow.add_edge(NodeStates.INVENTORY, END)
        workflow.add_edge(NodeStates.ORDERS, END)
        workflow.add_edge(NodeStates.GENERAL_RESPONSE, END)

        return workflow.compile()

    async def ainvoke(
        self,
        user_message: str,
        *,
        workflow_name: str | None = None,
        workflow_instance_id: str | None = None,
    ) -> dict:
        """
        Invokes the graph with a user message.

        Args:
            user_message (str): The current message from the user.
            workflow_name: Optional supervisor workflow name, threaded into
                graph state as an explicit fallback for MCP event identity.
            workflow_instance_id: Optional supervisor workflow instance id,
                threaded into graph state alongside workflow_name.

        Returns:
            str: The final state of the graph after processing the message.
        """
        inputs = {
            "messages": [user_message],
            "workflow_name": workflow_name,
            "workflow_instance_id": workflow_instance_id,
        }
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
