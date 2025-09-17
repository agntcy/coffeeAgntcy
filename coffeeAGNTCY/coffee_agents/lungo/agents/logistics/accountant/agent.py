# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from langgraph.graph import MessagesState
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, END

logger = logging.getLogger("lungo.accountant_agent.agent")


# --- 1. Define Node Names as Constants ---
class NodeStates:
    ACCOUNTANT = "accountant"


# --- 2. Define the Graph State ---
class GraphState(MessagesState):
    """
    Represents the state of our graph, passed between nodes.
    """
    pass


# --- 3. Implement the Accountant Agent Class ---
class AccountantAgent:
    def __init__(self):
        """
        Initializes the AccountantAgent with a single node LangGraph workflow.
        Handles one specific input:
        - CUSTOMS_CLEARANCE -> PAYMENT_COMPLETE
        Ignores all other inputs.
        """
        self.app = self._build_graph()

    # --- Node Definition ---

    def _accountant_node(self, state: GraphState) -> dict:
        """
        Single node that handles all accountant logic.
        """
        user_messages = state["messages"]

        # Extract the last message's content robustly
        if isinstance(user_messages, list) and user_messages:
            last_msg = user_messages[-1]
            # If it's a langchain message object, get .content; else, use as string
            if hasattr(last_msg, "content"):
                message_content = last_msg.content
            else:
                message_content = str(last_msg)
        else:
            message_content = str(user_messages)

        message_content = message_content.strip().upper()

        logger.info(f"Accountant agent received input: {message_content}")

        if "CUSTOMS_CLEARANCE" in message_content:
            logger.info("Processing CUSTOMS_CLEARANCE -> PAYMENT_COMPLETE")
            return {"messages": [AIMessage("PAYMENT_COMPLETE")]}
        else:
            logger.info("Ignoring unexpected input")
            return {"messages": [AIMessage("Accountant idle, no action taken.")]}

    # --- Graph Building Method ---

    def _build_graph(self):
        """
        Builds and compiles the LangGraph workflow with single node.
        """
        workflow = StateGraph(GraphState)

        # Add single node
        workflow.add_node(NodeStates.ACCOUNTANT, self._accountant_node)

        # Set the entry point
        workflow.set_entry_point(NodeStates.ACCOUNTANT)

        # Add edge to END
        workflow.add_edge(NodeStates.ACCOUNTANT, END)

        return workflow.compile()

    # --- Public Methods for Interaction ---

    async def ainvoke(self, user_message: str) -> str:
        """
        Invokes the graph with a user message.

        Args:
            user_message (str): The current message from the user.

        Returns:
            str: The final response from the accountant agent.
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
    agent = AccountantAgent()

    print("--- Testing Accountant Agent ---")
    test_messages = [
        "CUSTOMS_CLEARANCE",
        "customs_clearance",  # Test case insensitivity
        "PAYMENT_COMPLETE",
        "HANDOVER_TO_SHIPPER",
        "random message",
        "",
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
