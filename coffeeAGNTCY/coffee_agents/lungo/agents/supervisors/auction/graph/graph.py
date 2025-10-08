# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
import logging
import uuid

from pydantic import BaseModel, Field

from langchain_core.prompts import PromptTemplate
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from ioa_observe.sdk.decorators import agent, tool, graph

from agents.supervisors.auction.graph.tools import (
    get_farm_yield_inventory, 
    get_all_farms_yield_inventory,
    create_order, 
    get_order_details, 
    tools_or_next
)
from common.llm import get_llm

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

@agent(name="exchange_agent")
class ExchangeGraph:
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
            content="""You are an AI assistant reflecting on a conversation to determine if the user's request has been fully addressed.
            Review the entire conversation history provided.

            Decide whether the user's *original query* has been satisfied by the responses given so far.
            If the last message from the AI provides a conclusive answer to the user's request, or if the conversation has reached a natural conclusion, then set 'should_continue' to false.
            Do NOT continue if:
            - The last message from the AI is a final answer to the user's initial request.
            - The last message from the AI is a question that requires user input, and we are waiting for that input.
            - The conversation seems to be complete and no further action is explicitly requested or implied.
            - The conversation appears to be stuck in a loop or repeating itself (the 'is_duplicate_message' check will also help here).

            If more information is needed from the AI to fulfill the original request, or if the user has asked a follow-up question that needs an AI response, then set 'should_continue' to true.
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
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        # Find the last AIMessage that initiated tool calls
        last_ai_message = None
        for m in reversed(state["messages"]):
            if isinstance(m, AIMessage) and m.tool_calls:
                last_ai_message = m
                break

        collected_tool_messages = []
        if last_ai_message:
            # Get the IDs of the tool calls made by the last AI message
            tool_call_ids = {tc.get("id") for tc in last_ai_message.tool_calls if tc.get("id")}

            # Collect all ToolMessages that correspond to these tool_call_ids
            for m in reversed(state["messages"]):
                if isinstance(m, ToolMessage) and m.tool_call_id in tool_call_ids:
                    collected_tool_messages.append(m)

        tool_results_summary = []
        any_tool_failed = False # Flag to track if ANY tool call failed

        if collected_tool_messages:
            for tool_msg in collected_tool_messages:
                result_str = str(tool_msg.content) # Convert to string for keyword checking

                # Check for failure keywords in each individual tool result
                if "error" in result_str.lower() or \
                   "failed" in result_str.lower() or \
                   "timeout" in result_str.lower():
                    any_tool_failed = True
                    # Include tool name and ID for better context
                    tool_results_summary.append(f"FAILURE for '{tool_msg.name}' (ID: {tool_msg.tool_call_id}): The request could not be completed.")
                    logger.warning(f"Detected tool failure in result: {result_str}")
                else:
                    tool_results_summary.append(f"SUCCESS from tool '{tool_msg.name}' (ID: {tool_msg.tool_call_id}): {result_str}")

            context = "\n".join(tool_results_summary)
        else:
            context = "No previous tool execution context available."

        prompt = PromptTemplate(
            template="""You are an inventory broker for a global coffee exchange company.
            Your task is to provide accurate and concise information about coffee yields and inventory based on user queries.

            User's current request: {user_message}

            --- Context from previous tool execution (if any) ---
            {tool_context}

            --- Instructions for your response ---
            1.  **Process ALL tool results provided in the context.** This includes both successful and failed attempts.
            2.  **If ANY tool call result indicates a FAILURE:**
                *   Acknowledge the failure to the user for the specific farm(s)/request(s) that failed.
                *   Politely inform the user that the request could not be completed for those parts due to an issue (e.g., "The farm is currently unreachable", "An error occurred", or "The request failed for an unknown reason").
                *   **IMPORTANT: Do NOT include technical error messages, stack traces, or raw tool output details directly in your response to the user.** Summarize failures concisely.
                *   **Crucially, DO NOT attempt to call the same or any other tool again for any failed part of the request.**
                *   If other tool calls were successful, present their results clearly and concisely.
                *   Your response MUST synthesize all available information (successes and failures) into a single, comprehensive message.
                *   Your response MUST NOT contain any tool calls.

            3.  **If ALL tool call results indicate SUCCESS:**
                *   Summarize the provided information clearly and concisely to the user, directly answering their request.
                *   Your response MUST NOT contain any tool calls, as the information has already been obtained.

            4.  **If there is no 'Previous tool call result' (i.e., this is the first attempt):**
                *   Determine if a tool needs to be called to answer the user's question.
                *   If the user asks about a specific farm, use the `get_farm_yield_inventory` tool for that farm.
                *   If no farm was specified or the user asks about overall availability, use the `get_all_farms_yield_inventory` tool.
                *   If the question can be answered without a tool or requires clarification, provide that directly.

            Your final response should be a conclusive answer to the user's request, or a clear explanation if the request cannot be fulfilled.
            """,
            input_variables=["user_message", "tool_context"]
        )

        chain = prompt | self.inventory_llm

        llm_response = await chain.ainvoke({
            "user_message": user_msg.content if user_msg else "No specific user message.",
            "tool_context": context,
        })

        # --- Safety Net: Force non-tool-calling response if LLM ignores failure instruction ---
        # The safety net triggers if ANY tool failed in the previous step, e.g. one of the farm agent is offline when user asks for yield about multiple farms
        if any_tool_failed and llm_response.tool_calls:
            logger.warning(
                "LLM attempted tool call despite previous tool failure(s). "
                "Forcing a user-facing error message to prevent loop."
            )
            forced_error_message = (
                f"I encountered some issues retrieving information for your request. "
                f"Some parts could not be completed at this time due to a technical issue. "
                f"Please try again later."
            )
            llm_response = AIMessage(
                content=forced_error_message,
                tool_calls=[], # Crucially, no tool calls
                name=llm_response.name,
                id=llm_response.id,
                response_metadata=llm_response.response_metadata
            )
        # --- End Safety Net ---

        return {"messages": [llm_response]}

    async def _orders_node(self, state: GraphState) -> dict:
        """
        Handles orders-related queries using an LLM to formulate responses,
        with retry logic for tool failures.
        """
        if not self.orders_llm:
            self.orders_llm = get_llm().bind_tools([create_order, get_order_details])

        # Extract the latest HumanMessage for the prompt
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        # Find the last AIMessage that initiated tool calls
        last_ai_message = None
        for m in reversed(state["messages"]):
            if isinstance(m, AIMessage) and m.tool_calls:
                last_ai_message = m
                break

        collected_tool_messages = []
        if last_ai_message:
            tool_call_ids = {tc.get("id") for tc in last_ai_message.tool_calls if tc.get("id")}
            for m in reversed(state["messages"]):
                if isinstance(m, ToolMessage) and m.tool_call_id in tool_call_ids:
                    collected_tool_messages.append(m)

        tool_results_summary = []
        any_tool_failed = False # Flag to track if ANY tool call failed

        if collected_tool_messages:
            for tool_msg in collected_tool_messages:
                result_str = str(tool_msg.content) # Convert to string for keyword checking

                # Check for failure keywords in each individual tool result
                if "error" in result_str.lower() or \
                   "failed" in result_str.lower() or \
                   "timeout" in result_str.lower():
                    any_tool_failed = True
                    # Include tool name and ID for better context
                    tool_results_summary.append(f"FAILURE for '{tool_msg.name}' (ID: {tool_msg.tool_call_id}): The request could not be completed.")
                    logger.warning(f"Detected tool failure in orders node result: {result_str}")
                else:
                    tool_results_summary.append(f"SUCCESS from tool '{tool_msg.name}' (ID: {tool_msg.tool_call_id}): {result_str}")

            context = "\n".join(tool_results_summary)
        else:
            context = "No previous tool execution context available."

        prompt = PromptTemplate(
            template="""You are an orders broker for a global coffee exchange company.
            Your task is to handle user requests related to placing and checking orders with coffee farms.

            User's current request: {user_message}

            --- Context from previous tool execution (if any) ---
            {tool_context}

            --- Instructions for your response ---
            1.  **Process ALL tool results provided in the context.** This includes both successful and failed attempts.
            2.  **If ANY tool call result indicates a FAILURE:**
                *   Acknowledge the failure to the user for the specific request(s) that failed.
                *   Politely inform the user that the request could not be completed for those parts due to an issue (e.g., "The farm is currently unreachable" or "An error occurred").
                *   **IMPORTANT: Do NOT include technical error messages, stack traces, or raw tool output details directly in your response to the user.** Summarize failures concisely.
                *   **Crucially, DO NOT attempt to call the same or any other tool again for any failed part of the request.**
                *   If other tool calls were successful, present their results clearly and concisely.
                *   Your response MUST synthesize all available information (successes and failures) into a single, comprehensive message.
                *   Your response MUST NOT contain any tool calls.

            3.  **If ALL tool call results indicate SUCCESS:**
                *   Summarize the provided information clearly and concisely to the user, directly answering their request.
                *   Your response MUST NOT contain any tool calls, as the information has already been obtained.

            4.  **If there is no 'Previous tool call result' (i.e., this is the first attempt):**
                *   Determine if a tool needs to be called to answer the user's question.
                *   If the user asks about placing an order, use the `create_order` tool.
                *   If the user asks about checking the status of an order, use the `get_order_details` tool.
                *   If further information is needed to call a tool (e.g., missing order ID, quantity, farm), ask the user for clarification.

            Your final response should be a conclusive answer to the user's request, or a clear explanation if the request cannot be fulfilled.
            """,
            input_variables=["user_message", "tool_context"]
        )

        chain = prompt | self.orders_llm

        llm_response = await chain.ainvoke({
            "user_message": user_msg.content if user_msg else "No specific user message.",
            "tool_context": context,
        })

        # --- Safety Net: Force non-tool-calling response if LLM ignores failure instruction ---
        if any_tool_failed and llm_response.tool_calls:
            logger.warning(
                "LLM attempted tool call despite previous tool failure(s) in orders node. "
                "Forcing a user-facing error message to prevent loop."
            )

            forced_error_message = (
                f"I'm sorry, I was unable to complete your order request for all items. "
                f"An issue occurred for some parts. Please try again later."
            )

            llm_response = AIMessage(
                content=forced_error_message,
                tool_calls=[],
                name=llm_response.name,
                id=llm_response.id,
                response_metadata=llm_response.response_metadata
            )
        # --- End Safety Net ---

        return {"messages": [llm_response]}


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
