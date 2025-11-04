# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
import uuid
from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, END
from ioa_observe.sdk.decorators import agent, graph
from common.logistics_states import LogisticsStatus, extract_status, build_transition_message, ensure_order_id

logger = logging.getLogger("lungo.farm_agent.agent")

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

@agent(name="farm_agent")
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
            raw = getattr(last, "content", str(last)).strip()
        else:
            raw = str(messages).strip()

        status = extract_status(raw)
        order_id = ensure_order_id(raw)

        if status is LogisticsStatus.RECEIVED_ORDER:
            next_status = LogisticsStatus.HANDOVER_TO_SHIPPER
            msg = build_transition_message(
                order_id=order_id,
                sender="Tatooine Farm",
                receiver="Shipper",
                to_state=next_status.value,
                details="Prepared shipment and documentation",
            )
            return {"messages": [AIMessage(msg)]}

        return {"messages": [AIMessage("Logistic Farm remains IDLE. No further action required.")]}

    # --- Graph Building Method ---

    @graph(name="farm_graph")
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
        return messages[-1].content.strip()