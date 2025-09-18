# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
import uuid
from pydantic import BaseModel, Field

from langchain_core.prompts import PromptTemplate
from langchain_core.messages import AIMessage, SystemMessage

from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from ioa_observe.sdk.decorators import agent, tool, graph

from common.llm import get_llm
from agents.supervisors.logistic.graph.tools import (
    create_order,
    tools_or_next
)

logger = logging.getLogger("lungo.supervisor.graph")

class NodeStates:
    SUPERVISOR = "logistic_supervisor"

    ORDERS = "orders_broker"
    ORDERS_TOOLS = "orders_tools"

    REFLECTION = "reflection"
    GENERAL_INFO = "general"

class GraphState(MessagesState):
    """
    Represents the state of our graph, passed between nodes.
    """
    next_node: str

# @agent(name="logistic_agent")
class LogisticGraph:
    def __init__(self):
        self.graph = self.build_graph()

    # @graph(name="logistic_graph")
    def build_graph(self) -> CompiledStateGraph:
        """
        Constructs and compiles a LangGraph instance.

        Agent Flow:

        supervisor_agent
            - converse with user and coordinate app flow

        inventory_agent
            - get inventory for a specific farm or broadcast to all farms

        orders_agent
            - initiate orders with a specific farm and retrieve order status

        reflection_agent
            - determine if the user's request has been satisfied or if further action is needed

        Returns:
        CompiledGraph: A fully compiled LangGraph instance ready for execution.
        """

        self.supervisor_llm = None
        self.reflection_llm = None
        self.orders_llm = None

        workflow = StateGraph(GraphState)

        # --- 1. Define Node States ---

        workflow.add_node(NodeStates.SUPERVISOR, self._supervisor_node)
        workflow.add_node(NodeStates.ORDERS, self._orders_node)
        workflow.add_node(NodeStates.ORDERS_TOOLS, ToolNode([create_order]))
        workflow.add_node(NodeStates.REFLECTION, self._reflection_node)
        workflow.add_node(NodeStates.GENERAL_INFO, self._general_response_node)

        # --- 2. Define the Agentic Workflow ---

        workflow.set_entry_point(NodeStates.SUPERVISOR)

        # Add conditional edges from the supervisor
        workflow.add_conditional_edges(
            NodeStates.SUPERVISOR,
            lambda state: state["next_node"],
            {
                NodeStates.ORDERS: NodeStates.ORDERS,
                NodeStates.GENERAL_INFO: NodeStates.GENERAL_INFO,
            },
        )

        workflow.add_conditional_edges(NodeStates.ORDERS, tools_or_next(NodeStates.ORDERS_TOOLS, NodeStates.REFLECTION))
        workflow.add_edge(NodeStates.ORDERS_TOOLS, NodeStates.ORDERS)

        workflow.add_edge(NodeStates.GENERAL_INFO, END)
 
        return workflow.compile()
    
    async def _supervisor_node(self, state: GraphState) -> dict:
        """
        Determines the intent of the user's message and routes to the appropriate node.
        """
        if not self.supervisor_llm:
            self.supervisor_llm = get_llm()

        user_message = state["messages"]

        prompt = PromptTemplate(
            template="""You are a global coffee exchange agent connecting users to coffee farms in Brazil, Colombia, and Vietnam. 
            Based on the user's message, determine if it's related to 'inventory' or 'orders'.
            Respond with 'inventory' if the message is about checking yield, stock, product availability, regions of origin, or specific coffee item details.
            Respond with 'orders' if the message is about checking order status, placing an order, or modifying an existing order.
            
            User message: {user_message}
            """,
            input_variables=["user_message"]
        )

        chain = prompt | self.supervisor_llm
        response = chain.invoke({"user_message": user_message})
        intent = response.content.strip().lower()

        logger.info(f"Supervisor decided: {intent}")

        if "inventory" in intent:
            return {"next_node": NodeStates.INVENTORY, "messages": user_message}
        elif "orders" in intent:
            return {"next_node": NodeStates.ORDERS, "messages": user_message}
        else:
            return {"next_node": NodeStates.GENERAL_INFO, "messages": user_message}
        
    async def _reflection_node(self, state: GraphState) -> dict:
        """
        Reflect on the conversation to determine if the user's query has been satisfied 
        or if further action is needed.
        """
        if not self.reflection_llm:
            class ShouldContinue(BaseModel):
                should_continue: bool = Field(description="Whether to continue processing the request.")
                reason: str = Field(description="Reason for decision whether to continue the request.")
            
            # create a structured output LLM for reflection
            self.reflection_llm = get_llm().with_structured_output(ShouldContinue, strict=True)

        sys_msg_reflection = SystemMessage(
            content="""Decide whether the user query has been satisifed or if we need to continue.
                Do not continue if the last message is a question or requires user input.
                """,
                pretty_repr=True,
            )
        
        response = await self.reflection_llm.ainvoke(
          [sys_msg_reflection] + state["messages"]
        )
        logging.info(f"Reflection agent response: {response}")

        is_duplicate_message = (
          len(state["messages"]) > 2 and state["messages"][-1].content == state["messages"][-3].content
        )
        
        should_continue = response.should_continue and not is_duplicate_message
        next_node = NodeStates.SUPERVISOR if should_continue else END
        logging.info(f"Next node: {next_node}")

        return {
          "next_node": next_node,
          "messages": [SystemMessage(content=response.reason)],
        }

    async def _orders_node(self, state: GraphState) -> dict:
        if not self.orders_llm:
            self.orders_llm = get_llm().bind_tools([create_order])

        prompt = PromptTemplate(
            template=(
                "You are an orders broker for a global coffee exchange company. "
                "You handle user requests about placing and checking orders with coffee farms.\n\n"
                "Rules:\n"
                "1. Always call the create_order tool.\n"
                "2. If the user wants order status, retrieve or summarize it.\n"
                "3. Do not create a duplicate order for the same request.\n"
                "4. Ask for clarification only when required.\n"
                "5. FINAL DELIVERY HANDLING:\n"
                "   If any earlier tool or agent message contains the exact token 'DELIVERED' "
                "(indicates the order was fully delivered), DO NOT call tools again and DO NOT ask questions. "
                "Respond ONLY with a multiline plain text summary in the following format without any newline character (and nothing else):\n"
                "   Order ORD-XXXXXXXX from <farm or unknown> for <quantity or unknown> units at <price or unknown> has been successfully delivered."
                "   - Generate Order ID as ORD- followed by 8 uppercase hex characters.\n"
                "   - Infer farm / quantity / price from prior messages; if missing use 'unknown'.\n"
                "   - Never call tools after 'DELIVERED' appears.\n\n"
                "Output:\n"
                "- Normal flow: helpful answer or tool call.\n"
                "- Delivery flow: ONLY the specified formatted text block.\n\n"
                "Conversation messages:\n"
                "{user_message}"
            ),
            input_variables=["user_message"]
        )

        chain = prompt | self.orders_llm

        llm_response = chain.invoke({
            "user_message": state["messages"],
        })

        if llm_response.tool_calls:
            logger.info(f"Tool calls detected from orders_node: {llm_response.tool_calls}")
            logger.debug(f"Messages: {state['messages']}")
        return {
            "messages": [llm_response]
        }
    
    def _general_response_node(self, state: GraphState) -> dict:
        return {
            "next_node": END,
            "messages": [AIMessage(content="I'm not sure how to handle that. Could you please clarify?")],
        }

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

            messages = result.get("messages", [])
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