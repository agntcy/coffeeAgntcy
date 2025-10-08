# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, END

from ioa_observe.sdk.decorators import agent, graph

from common.llm import get_llm

logger = logging.getLogger("lungo.brazil_farm_agent.agent")

# --- 1. Define Node Names as Constants ---
class NodeStates:
    SUPERVISOR = "supervisor"
    INVENTORY = "inventory_node"
    ORDERS = "orders_node"
    GENERAL_RESPONSE = "general_response_node"

# --- 2. Define the Graph State ---
class GraphState(MessagesState):
    """
    Represents the state of our graph, passed between nodes.
    """
    next_node: str

# --- 3. Implement the LangGraph Application Class ---
@agent(name="brazil_farm_agent")
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

        self.app = self._build_graph()

    # --- Node Definitions ---

    def _supervisor_node(self, state: GraphState) -> dict:
        """
        Determines the intent of the user's message and routes to the appropriate node.
        """
        if not self.supervisor_llm:
            self.supervisor_llm = get_llm()

        prompt = PromptTemplate(
            template="""You are a coffee farm manager in Brazil who delegates farm cultivation and global sales. Based on the 
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
            return {"next_node": NodeStates.INVENTORY, "messages": state["messages"]}
        elif "orders" in intent:
            return {"next_node": NodeStates.ORDERS, "messages": state["messages"]}
        else:
            return {"next_node": NodeStates.GENERAL_RESPONSE, "messages": state["messages"]}

    def _inventory_node(self, state: GraphState) -> dict:
        """
        Handles inventory-related queries using an LLM to formulate responses.
        """
        if not self.inventory_llm:
            self.inventory_llm = get_llm()

        user_message = state["messages"]

        prompt = PromptTemplate(
            template="""You are a helpful coffee farm cultivation manager in Brazil who handles yield or inventory requets. 
            Your job is to:
            1. Return a random yield estimate for the coffee farm in Brazil. Make sure the estimate is a reasonable value and in pounds.
            2. Respond with only the yield estimate.\n

            If the user asked in lbs or pounds, respond with the estimate in pounds. If the user asked in kg or kilograms, convert the estimate to kg and respond with that value.\n

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

    def _general_response_node(self, state: GraphState) -> dict:
        """
        Provides a fallback response for unclear or out-of-scope messages.
        """
        response = "I'm designed to help with inventory and order-related questions. Could you please rephrase your request?"
        return {"messages": [AIMessage(response)]}

    # --- Graph Building Method ---

    @graph(name="brazil_farm_graph")
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

        # Set the entry point
        workflow.set_entry_point(NodeStates.SUPERVISOR)

        # Add conditional edges from the supervisor
        workflow.add_conditional_edges(
            NodeStates.SUPERVISOR,
            lambda state: state["next_node"],
            {
                NodeStates.INVENTORY: NodeStates.INVENTORY,
                NodeStates.ORDERS: NodeStates.ORDERS,
                NodeStates.GENERAL_RESPONSE: NodeStates.GENERAL_RESPONSE,
            },
        )

        # Add edges from the specific nodes to END
        workflow.add_edge(NodeStates.INVENTORY, END)
        workflow.add_edge(NodeStates.ORDERS, END)
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

    print("--- Testing Inventory Queries ---")
    messages = [
        "How much coffee do we have in stock?",
        "What is the current yield estimate?",
    ]
    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await agent.ainvoke(msg)
        print(f"Agent: {final_state}")

    print("\n" + "="*50 + "\n")


    messages = [
        "Can you order me 100 lbs of coffee?",
        "I want to place a new order for 50 kg of coffee",
    ]
    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await agent.ainvoke(msg)
        print(f"Agent: {final_state}")

    print("\n" + "="*50 + "\n")

    messages = [
        "Tell me a joke.",
        "What's the weather like today?",
    ]
    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await agent.ainvoke(msg)
        print(f"Agent: {final_state}")

# --- Example Usage ---
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())