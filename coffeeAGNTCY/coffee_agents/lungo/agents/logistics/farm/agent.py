# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from langgraph.graph import MessagesState
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, END
from common.logistic_states import (
    LogisticStatus,
    extract_status,
)

logger = logging.getLogger("lungo.shipper_agent.agent")


# --- 1. Define Node Names as Constants ---
class NodeStates:
    FARM = "farm"


# --- 2. Define the Graph State ---
class GraphState(MessagesState):
    """
    Represents the state of our graph, passed between nodes.
    """
    pass


# --- 3. Implement the Shipper Agent Class ---
class FarmAgent:
    def __init__(self):
        """
        Initializes the FarmAgent with a single node LangGraph workflow.
        Handles two specific inputs:
        - HANDOVER_TO_SHIPPER -> CUSTOMS_CLEARANCE
        - PAYMENT_COMPLETE -> DELIVERED
        """
        self.app = self._build_graph()

    # --- Node Definition ---

    def _farm_node(self, state: GraphState) -> dict:
        messages = state["messages"]
        if isinstance(messages, list) and messages:
            last = messages[-1]
            text = getattr(last, "content", str(last))
        else:
            text = str(messages)
        raw = text.strip()
        status = extract_status(raw)

        if status is LogisticStatus.RECEIVED_ORDER:
            next_status = LogisticStatus.HANDOVER_TO_SHIPPER
            return {"messages": [AIMessage(next_status.value)]}

        idle_msg = (
            f"Action '{None}' received. No shipper handling required. "
            "Shipper remains IDLE. No further action required."
        )
        return {"messages": [AIMessage(idle_msg)]}

    # --- Graph Building Method ---

    def _build_graph(self):
        """
        Builds and compiles the LangGraph workflow with single node.
        """
        workflow = StateGraph(GraphState)

        # Add single node
        workflow.add_node(NodeStates.FARM, self._farm_node)

        # Set the entry point
        workflow.set_entry_point(NodeStates.FARM)

        # Add edge to END
        workflow.add_edge(NodeStates.FARM, END)

        return workflow.compile()

    # --- Public Methods for Interaction ---

    async def ainvoke(self, user_message: str) -> str:
        """
        Invokes the graph with a user message.

        Args:
            user_message (str): The current message from the user.

        Returns:
            str: The final response from the shipper agent.
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
    agent = FarmAgent()

    print("--- Testing Shipper Agent ---")
    test_messages = [
        "HANDOVER_TO_SHIPPER",
        "PAYMENT_COMPLETE",
        "INVALID_INPUT",
        "handover_to_shipper",  # Test case sensitivity
        "payment_complete",  # Test case sensitivity
        "random message",
    ]

    for msg in test_messages:
        print(f"\nInput: {msg}")
        try:
            response = await agent.ainvoke(msg)
            print(f"Output: {response}")
        except Exception as e:
            print(f"Error: {e}")


# --- Example Usage ---
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
