# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, END

from ioa_observe.sdk.decorators import agent, graph

from common.logistics_states import (
    LogisticsStatus,
    extract_status,
    build_transition_message,
    ensure_order_id,
)

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
@agent(name="accountant_agent")
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
        Transitions:
          CUSTOMS_CLEARANCE -> PAYMENT_COMPLETE
        """
        messages = state["messages"]
        if isinstance(messages, list) and messages:
            last = messages[-1]
            raw = getattr(last, "content", str(last)).strip()
        else:
            raw = str(messages).strip()

        status = extract_status(raw)
        order_id = ensure_order_id(raw)

        if status is LogisticsStatus.CUSTOMS_CLEARANCE:
            next_status = LogisticsStatus.PAYMENT_COMPLETE
            msg = build_transition_message(
                order_id=order_id,
                sender="Accountant",
                receiver="Shipper",
                to_state=next_status.value,
                details="Payment verified and captured",
            )
            return {"messages": [AIMessage(msg)]}

        return {"messages": [AIMessage("Accountant remains IDLE. No further action required.")]}

    # --- Graph Building Method ---
    @graph(name="accountant_graph")
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
        return messages[-1].content.strip()