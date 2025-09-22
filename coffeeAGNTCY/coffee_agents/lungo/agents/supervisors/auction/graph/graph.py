# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import uuid
from typing import Optional
from pydantic import BaseModel, Field

from langchain_core.prompts import PromptTemplate
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage, HumanMessage

from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from ioa_observe.sdk.decorators import agent, tool, graph

from common.llm import get_llm
from graph.tools import (
    get_farm_yield_inventory, 
    get_all_farms_yield_inventory,
    create_order, 
    get_order_details, 
    tools_or_next
)

logger = logging.getLogger("lungo.supervisor.graph")

class NodeStates:
    SUPERVISOR = "exchange_supervisor"

    INVENTORY = "inventory_broker"
    INVENTORY_TOOLS = "inventory_tools"

    ORDERS = "orders_broker"
    ORDERS_TOOLS = "orders_tools"

    REFLECTION = "reflection"
    GENERAL_INFO = "general"

class GraphState(MessagesState):
    """
    Represents the state of our graph, passed between nodes.
    """
    next_node: str
    inventory_tool_retry_count: int
    orders_tool_retry_count: int
    last_inventory_tool_error: Optional[str]
    last_orders_tool_error: Optional[str]

@agent(name="exchange_agent")
class ExchangeGraph:
    DEFAULT_MAX_TOOL_RETRIES = 3
    try:
        MAX_TOOL_RETRIES = int(os.getenv("MAX_TOOL_RETRIES", str(DEFAULT_MAX_TOOL_RETRIES)))
        if MAX_TOOL_RETRIES < 0:
            raise ValueError("MAX_TOOL_RETRIES cannot be negative.")
    except ValueError:
        logger.warning(
            f"Invalid value for MAX_TOOL_RETRIES environment variable. "
            f"Using default of {DEFAULT_MAX_TOOL_RETRIES}."
        )
        MAX_TOOL_RETRIES = DEFAULT_MAX_TOOL_RETRIES

    def __init__(self):
        self.graph = self.build_graph()

    @graph(name="exchange_graph")
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
        self.inventory_llm = None
        self.orders_llm = None

        workflow = StateGraph(GraphState)

        # --- 1. Define Node States ---

        workflow.add_node(NodeStates.SUPERVISOR, self._supervisor_node)
        workflow.add_node(NodeStates.INVENTORY, self._inventory_node)
        workflow.add_node(NodeStates.INVENTORY_TOOLS, ToolNode([get_farm_yield_inventory, get_all_farms_yield_inventory]))
        workflow.add_node(NodeStates.ORDERS, self._orders_node)
        workflow.add_node(NodeStates.ORDERS_TOOLS, ToolNode([create_order, get_order_details]))
        workflow.add_node(NodeStates.REFLECTION, self._reflection_node)
        workflow.add_node(NodeStates.GENERAL_INFO, self._general_response_node)

        # --- 2. Define the Agentic Workflow ---

        workflow.set_entry_point(NodeStates.SUPERVISOR)

        # Add conditional edges from the supervisor
        workflow.add_conditional_edges(
            NodeStates.SUPERVISOR,
            lambda state: state["next_node"],
            {
                NodeStates.INVENTORY: NodeStates.INVENTORY,
                NodeStates.ORDERS: NodeStates.ORDERS,
                NodeStates.GENERAL_INFO: NodeStates.GENERAL_INFO,
            },
        )

        workflow.add_conditional_edges(NodeStates.INVENTORY, tools_or_next(NodeStates.INVENTORY_TOOLS, NodeStates.REFLECTION))
        workflow.add_edge(NodeStates.INVENTORY_TOOLS, NodeStates.INVENTORY)

        workflow.add_conditional_edges(NodeStates.ORDERS, tools_or_next(NodeStates.ORDERS_TOOLS, NodeStates.REFLECTION))
        workflow.add_edge(NodeStates.ORDERS_TOOLS, NodeStates.ORDERS)

        workflow.add_edge(NodeStates.GENERAL_INFO, END)
        workflow.add_edge(NodeStates.REFLECTION, END) # Reflection decides if conversation ends or loops to supervisor

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

        # Check for error messages
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage):
            error_keywords = ["error", "unavailable", "issue", "failed", "unresponsive"]
            if any(keyword in last_message.content.lower() for keyword in error_keywords):
                logger.info(f"Reflection agent detected error message in last AIMessage: {last_message.content}. Ending conversation.")
                return {
                    "next_node": END,
                    "messages": [SystemMessage(content="Conversation ended due to tool error or service unavailability.")]
                }

        sys_msg_reflection = SystemMessage(
            content="""Decide whether the user query has been satisfied or if we need to continue.
                Do not continue if the last message is a question or requires user input.
                Also, do not continue if the last message is an error message indicating a tool failure or service unavailability, as this means the request cannot be fulfilled at this time.
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

    async def _inventory_node(self, state: GraphState) -> dict:
        """
        Handles inventory-related queries using an LLM to formulate responses.
        """
        if not self.inventory_llm:
            self.inventory_llm = get_llm().bind_tools(
                [get_farm_yield_inventory, get_all_farms_yield_inventory],
                strict=True
            )
        
        # get latest HumanMessage
        user_msg = next(
            (m for m in reversed(state["messages"]) if m.type == "human"), None
        )

        # Find the AIMessage that initiated the tool calls
        initiating_ai_message = None
        for i in reversed(range(len(state["messages"]))):
            msg = state["messages"][i]
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                initiating_ai_message = msg
                break

        # Collect all ToolMessages that correspond to the tool calls from the initiating_ai_message
        relevant_tool_responses = []
        if initiating_ai_message:
            expected_tool_call_ids = {tc["id"] for tc in initiating_ai_message.tool_calls}
            for i in reversed(range(len(state["messages"]))):
                msg = state["messages"][i]
                if isinstance(msg, ToolMessage) and msg.tool_call_id in expected_tool_call_ids:
                    relevant_tool_responses.append(msg)
                # Stop collecting once we pass the initiating AIMessage or another HumanMessage
                if msg is initiating_ai_message or isinstance(msg, HumanMessage):
                    break
            relevant_tool_responses.reverse()

        is_error = False
        aggregated_errors = []
        error_keywords = ["error", "exception", "failed", "unavailable",
                          "issue", "noresponderserror", "not recognized"]

        if relevant_tool_responses:
            for tool_response_msg in relevant_tool_responses:
                # Check if the tool_response_msg content indicates an error
                if any(keyword in tool_response_msg.content.lower() for keyword
                       in error_keywords):
                    is_error = True
                    aggregated_errors.append(tool_response_msg.content)

            if is_error:
                last_error = "\n".join(aggregated_errors)
                logger.error(f"Tool execution failed in _inventory_node. Aggregated errors: {last_error}")
            else:
                last_error = None  # Clear last_error if no errors detected in this batch
        else:
            # If there were no relevant tool responses, it means no tools were called or they haven't returned yet.
            # In this case, we don't have an error from tool execution.
            last_error = state["last_inventory_tool_error"]

        current_retry_count = state["inventory_tool_retry_count"]

        if is_error and current_retry_count >= self.MAX_TOOL_RETRIES:
            logger.warning(f"Inventory tool failed after {self.MAX_TOOL_RETRIES} attempts, "
                           f"details: {last_error or 'No specific error details available.'}. Giving up.")

            user_friendly_error_message = (
                "I encountered an issue while trying to fetch inventory information after multiple attempts. "
                "It seems the inventory service is currently unavailable or unresponsive. "
                "Please try again later or contact support if the problem persists. "
            )
            # Reset retry count and error for future interactions
            state_update_on_failure = {
                "inventory_tool_retry_count": 0,
                "last_inventory_tool_error": None
            }
            return {
                "messages": state["messages"] + [AIMessage(content=user_friendly_error_message, tool_calls=[])],
                **state_update_on_failure
            }


        state_update = {
            "inventory_tool_retry_count": current_retry_count,
            "last_inventory_tool_error": last_error
        }

        prompt_parts = []
        prompt_parts.append("""You are an inventory broker for a global coffee exchange company. 
            Your task is to provide accurate and concise information about coffee yields and inventory based on user queries.
            """)

        if is_error: # This block is now only entered if current_retry_count < self.MAX_TOOL_RETRIES
            logger.warning(f"Inventory tool failed. Retrying... Attempt {current_retry_count + 1}/{self.MAX_TOOL_RETRIES}")
            state_update["inventory_tool_retry_count"] = current_retry_count + 1
            prompt_parts.append(f"""
            The previous attempt to get inventory information failed with the following error: "{last_error or 'an unknown error'}".
            Please try again to use the appropriate tool(s) to fulfill the user's request.
            """)
        else: # No error, or successful tool call, or first attempt
            state_update["inventory_tool_retry_count"] = 0
            state_update["last_inventory_tool_error"] = None
            # Aggregate content from all relevant tool responses for the LLM to summarize
            aggregated_tool_response_content = "\n".join([msg.content for msg in relevant_tool_responses])
            if aggregated_tool_response_content: # Only add if there was actual tool output
                prompt_parts.append(f"""
                Tools have just executed and responded with: {aggregated_tool_response_content}
                Based on this information, summarize the outcome of the inventory query to the user.
                Crucially, if the user's request has been fully addressed by this tool output, provide the summary and DO NOT generate any new tool calls.
                If the user asks for *different* information that requires a new tool call, then generate that new tool call.
                """)
            else: # No tool response yet, or first attempt after a reset
                prompt_parts.append("""
                If the user asks about how much coffee we have, what the yield is or general coffee inventory, use the provided tools.
                If no farm was specified, use the get_all_farms_yield_inventory tool to get the total yield across all farms.
                If the user asks about a specific farm, use the get_farm_yield_inventory tool to get the yield for that farm.
                If the user asks where we have coffee available, get the yield from all farms and respond with the total yield across all farms.
                """)

        prompt_parts.append(f"User question: {user_msg.content if user_msg else ''}")

        prompt = PromptTemplate(
            template="\n".join(prompt_parts),
            input_variables=["user_message"]
        )

        chain = prompt | self.inventory_llm

        llm_response = await chain.ainvoke({
            "user_message": user_msg.content if user_msg else '',
        })

        new_messages = state["messages"] + [llm_response]

        return {
            "messages": new_messages,
            **state_update
        }
    
    async def _orders_node(self, state: GraphState) -> dict:
        """
        Handles orders-related queries using an LLM to formulate responses,
        with retry logic for tool failures.
        """
        if not self.orders_llm:
            self.orders_llm = get_llm().bind_tools([create_order, get_order_details])

        user_msg = next(
            (m for m in reversed(state["messages"]) if m.type == "human"), None
        )

        initiating_ai_message = None
        for i in reversed(range(len(state["messages"]))):
            msg = state["messages"][i]
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                initiating_ai_message = msg
                break

        relevant_tool_responses = []
        if initiating_ai_message:
            expected_tool_call_ids = {tc["id"] for tc in initiating_ai_message.tool_calls}
            for i in reversed(range(len(state["messages"]))):
                msg = state["messages"][i]
                if isinstance(msg, ToolMessage) and msg.tool_call_id in expected_tool_call_ids:
                    relevant_tool_responses.append(msg)
                if msg is initiating_ai_message or (isinstance(msg, HumanMessage) and msg is not user_msg):
                    break
            relevant_tool_responses.reverse()

        current_retry_count = state["orders_tool_retry_count"]
        last_error = state["last_orders_tool_error"]

        is_error = False
        aggregated_errors = []
        error_keywords = ["error", "exception", "failed", "unavailable",
                          "issue", "noresponderserror",
                          "identity verification failed"]

        if relevant_tool_responses:
            for tool_response_msg in relevant_tool_responses:
                if any(keyword in tool_response_msg.content.lower() for keyword
                       in error_keywords):
                    is_error = True
                    aggregated_errors.append(tool_response_msg.content)

            if is_error:
                last_error = "\n".join(aggregated_errors)
                logger.error(
                    f"Tool execution failed in _orders_node. Aggregated errors: {last_error}")
            elif not is_error and relevant_tool_responses:
                last_error = None

        if is_error and current_retry_count >= self.MAX_TOOL_RETRIES:
            logger.warning(
                f"Orders tool failed after {self.MAX_TOOL_RETRIES} attempts,"
                f"details: {last_error or 'No specific error details available.'}. Giving up.")

            user_friendly_error_message = (
                "I encountered an issue while trying to process your order after multiple attempts. "
                "It seems the order service is currently unavailable or unresponsive. "
                "Please try again later or contact support if the problem persists. "
            )

            state_update_on_failure = {
                "orders_tool_retry_count": 0,
                "last_orders_tool_error": None
            }

            return {
                "messages": state["messages"] + [AIMessage(content=user_friendly_error_message, tool_calls=[])],
                **state_update_on_failure
            }

        state_update = {"orders_tool_retry_count": current_retry_count,
            "last_orders_tool_error": last_error}

        prompt_parts = []
        prompt_parts.append("""You are an orders broker for a global coffee exchange company. 
            Your task is to handle user requests related to placing and checking orders with coffee farms.
            """)

        if is_error:  # This block is now only entered if current_retry_count < self.MAX_TOOL_RETRIES
            logger.info(f"Orders tool failed. Retrying... Attempt {current_retry_count + 1}/{self.MAX_TOOL_RETRIES}")
            state_update["orders_tool_retry_count"] = current_retry_count + 1
            prompt_parts.append(f"""
            The previous attempt to process the order failed with the following error: "{last_error or 'an unknown error'}".
            Please try again to use the appropriate tool(s) to fulfill the user's request.
            """)
        else:  # No error, or successful tool call, or first attempt
            state_update["orders_tool_retry_count"] = 0
            state_update["last_orders_tool_error"] = None
            aggregated_tool_response_content = "\n".join(
                [msg.content for msg in relevant_tool_responses])
            if aggregated_tool_response_content:
                prompt_parts.append(f"""
                Tools have just executed and responded with: {aggregated_tool_response_content}
                Based on this information, summarize the outcome of the order query to the user.
                Crucially, if the user's request has been fully addressed by this tool output, provide the summary and DO NOT generate any new tool calls.
                If the user asks for *different* information that requires a new tool call, then generate that new tool call.
                """)
            else:
                prompt_parts.append("""
                If the issue is related to identity verification, respond with a short reply: 
                'The badge of this <current_farm> farm agent has not been found or could not be verified, and hence the order request failed.' 
                Do not ask further questions in this case.

                If the user asks about placing an order, use the provided tools to create an order.
                If the user asks about checking the status of an order, use the provided tools to retrieve order details.
                If an order has been created, do not create a new order for the same request.
                If further information is needed, ask the user for clarification.
                """)

        prompt_parts.append(
            f"User question: {user_msg.content if user_msg else ''}")

        prompt = PromptTemplate(template="\n".join(prompt_parts),
                                input_variables=["user_message"])

        chain = prompt | self.orders_llm

        llm_response = await chain.ainvoke(
            {"user_message": user_msg.content if user_msg else '', })

        new_messages = state["messages"] + [llm_response]

        if llm_response.tool_calls:
            logger.info(f"Tool calls detected from orders_node: {llm_response.tool_calls}")
            logger.debug(f"Messages: {state['messages']}")
        return {"messages": new_messages, **state_update}

    def _general_response_node(self, state: GraphState) -> dict:
        return {
            "next_node": END,
            "messages": state["messages"],
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
            initial_state = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "inventory_tool_retry_count": 0,
                "orders_tool_retry_count": 0,
                "last_inventory_tool_error": None,
                "last_orders_tool_error": None,
            }
            result = await self.graph.ainvoke(
                initial_state,
                {"configurable": {"thread_id": uuid.uuid4()}}
            )

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