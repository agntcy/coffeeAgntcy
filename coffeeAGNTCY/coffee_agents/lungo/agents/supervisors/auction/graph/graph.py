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
from langgraph.config import get_stream_writer
from ioa_observe.sdk.decorators import agent, tool, graph

from agents.supervisors.auction.graph.tools import (
    get_farm_yield_inventory,
    get_all_farms_yield_inventory,
    get_all_farms_yield_inventory_streaming,
    get_fake_stream_data_tool,
    create_order,
    get_order_details,
    tools_or_next
)
from common.llm import get_llm

logger = logging.getLogger("lungo.supervisor.graph")

class NodeStates:
    SUPERVISOR = "exchange_supervisor"

    INVENTORY_SINGLE_FARM = "inventory_single_farm"
    INVENTORY_ALL_FARMS = "inventory_all_farms"

    ORDERS = "orders_broker"
    ORDERS_TOOLS = "orders_tools"

    REFLECTION = "reflection"
    GENERAL_INFO = "general"

class GraphState(MessagesState):
    """
    Represents the state of our graph, passed between nodes.
    """
    next_node: str
    full_response: str = ""

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

        inventory_single_farm_agent
            - get inventory for a specific farm
        
        inventory_all_farms_agent
            - broadcast to all farms and aggregate inventory

        orders_agent
            - initiate orders with a specific farm and retrieve order status

        reflection_agent
            - determine if the user's request has been satisfied or if further action is needed

        Returns:
        CompiledGraph: A fully compiled LangGraph instance ready for execution.
        """

        self.supervisor_llm = None
        self.reflection_llm = None
        self.inventory_single_farm_llm = None
        self.inventory_all_farms_llm = None
        self.orders_llm = None

        workflow = StateGraph(GraphState)

        # --- 1. Define Node States ---

        workflow.add_node(NodeStates.SUPERVISOR, self._supervisor_node)
        workflow.add_node(NodeStates.INVENTORY_SINGLE_FARM, self._inventory_single_farm_node)
        workflow.add_node(NodeStates.INVENTORY_ALL_FARMS, self._inventory_all_farms_node)
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
                NodeStates.INVENTORY_SINGLE_FARM: NodeStates.INVENTORY_SINGLE_FARM,
                NodeStates.INVENTORY_ALL_FARMS: NodeStates.INVENTORY_ALL_FARMS,
                NodeStates.ORDERS: NodeStates.ORDERS,
                NodeStates.GENERAL_INFO: NodeStates.GENERAL_INFO,
            },
        )

        workflow.add_edge(NodeStates.INVENTORY_SINGLE_FARM, NodeStates.REFLECTION)
        workflow.add_edge(NodeStates.INVENTORY_ALL_FARMS, NodeStates.REFLECTION)

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
            Based on the user's message, determine the appropriate action:
            
            - Respond with 'inventory_single_farm' if the user asks about a SPECIFIC farm (Brazil, Colombia, or Vietnam)
            - Respond with 'inventory_all_farms' if the user asks about inventory/yield from ALL farms or doesn't specify a farm
            - Respond with 'orders' if the message is about checking coffee order status, placing a coffee order, or modifying an existing coffee order
            - Respond with 'none of the above' if the message is unrelated to coffee 'inventory' or 'orders'
            
            User message: {user_message}
            """,
            input_variables=["user_message"]
        )

        chain = prompt | self.supervisor_llm
        response = chain.invoke({"user_message": user_message})
        intent = response.content.strip().lower()

        logger.info(f"Supervisor decided: {intent}")

        if "inventory_single_farm" in intent:
            return {"next_node": NodeStates.INVENTORY_SINGLE_FARM, "messages": user_message}
        elif "inventory_all_farms" in intent:
            return {"next_node": NodeStates.INVENTORY_ALL_FARMS, "messages": user_message}
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
        logging.info(f"Next node: {next_node}, Reason: {response.reason}")

        # Don't add messages to state, just return the next_node decision
        return {
          "next_node": next_node,
        }

    async def _inventory_single_farm_node(self, state: GraphState) -> dict:
        """
        Handles inventory queries for a specific farm by directly calling the tool.
        """
        if not self.inventory_single_farm_llm:
            self.inventory_single_farm_llm = get_llm()

        # Get latest HumanMessage
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        if not user_msg:
            return {"messages": [AIMessage(content="No user message found.")]}

        user_query = user_msg.content.lower()
        logger.info(f"Processing single farm inventory query: {user_query}")

        # Determine which farm
        farm = None
        if "brazil" in user_query:
            farm = "brazil"
        elif "colombia" in user_query:
            farm = "colombia"
        elif "vietnam" in user_query:
            farm = "vietnam"

        if not farm:
            return {"messages": [AIMessage(content="Please specify which farm you'd like to query (Brazil, Colombia, or Vietnam).")]}

        try:
            # Call the function directly
            tool_result = await get_farm_yield_inventory(user_msg.content, farm)
            
            # Check for errors in the result
            if "error" in str(tool_result).lower() or "failed" in str(tool_result).lower():
                error_message = f"I encountered an issue retrieving information from the {farm.title()} farm. Please try again later."
                return {"messages": [AIMessage(content=error_message)]}

            # Use LLM to format the response
            prompt = PromptTemplate(
                template="""You are an inventory broker for a global coffee exchange company.
                The user asked about inventory from the {farm} farm.
                
                User's request: {user_message}
                
                Farm response:
                {tool_result}
                
                Please provide a clear and concise response to the user based on the farm's inventory information.
                """,
                input_variables=["farm", "user_message", "tool_result"]
            )

            chain = prompt | self.inventory_single_farm_llm
            llm_response = await chain.ainvoke({
                "farm": farm.title(),
                "user_message": user_msg.content,
                "tool_result": tool_result,
            })

            return {"messages": [AIMessage(content=llm_response.content)]}

        except Exception as e:
            logger.error(f"Error in single farm inventory node: {e}")
            error_message = f"I encountered an issue retrieving information from the {farm.title()} farm. Please try again later."
            return {"messages": [AIMessage(content=error_message)]}

    # async def _inventory_all_farms_node(self, state: GraphState) -> dict:
    #     """
    #     Handles inventory queries for all farms by directly calling the function and returning the result.
    #     """
    #     # Get latest HumanMessage
    #     user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
    #     if not user_msg:
    #         return {"messages": [AIMessage(content="No user message found.")]}
    #
    #     logger.info(f"Processing all farms inventory query: {user_msg.content}")
    #
    #     try:
    #         # Call the function directly and return the result
    #         tool_result = await get_all_farms_yield_inventory(user_msg.content)
    #         return {"messages": [AIMessage(content=tool_result)]}
    #
    #     except Exception as e:
    #         logger.error(f"Error in all farms inventory node: {e}")
    #         error_message = "I encountered an issue retrieving information from the farms. Please try again later."
    #         return {"messages": [AIMessage(content=error_message)]}

    async def _inventory_all_farms_node(self, state: GraphState) -> dict:
        """
        Handles inventory queries for all farms using the fake stream data tool.
        Yields chunks progressively as they arrive using StreamWriter if available.
        """
        # Get latest HumanMessage
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        if not user_msg:
            yield {"messages": [AIMessage(content="No user message found.")]}

        logger.info(f"Processing all farms inventory query: {user_msg.content}")

        try:
            # Stream data from farms and yield each chunk progressively
            full_response = ""
            async for chunk in get_all_farms_yield_inventory_streaming(user_msg.content):
                yield {"messages": [AIMessage(content=chunk.strip())]}
                full_response += chunk
            
            # Yield final aggregated response with full_response key
            yield {"messages": [AIMessage(content=full_response.strip())], "full_response": full_response.strip()}

        except Exception as e:
            logger.error(f"Error in all farms inventory node: {e}")
            error_message = "I encountered an issue retrieving information from the farms. Please try again later."
            yield {"messages": [AIMessage(content=error_message)]}

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

    async def streaming_serve(self, prompt: str):
        """
        Streams the graph execution, yielding chunks as they arrive.
        Handles special streaming mode for progressive data delivery.

        Args:
            prompt (str): The input prompt to be processed by the graph.

        Yields:
            str: Chunks of output as they arrive from nodes and tools.
        """
        try:
            logger.debug(f"Received streaming prompt: {prompt}")
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("Prompt must be a non-empty string.")

            # Regular non-streaming flow
            state = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            }

            seen_contents = set()
            async for event in self.graph.astream_events(state, {"configurable": {"thread_id": uuid.uuid4()}}, version="v2"):
                # Handle different event types
                logger.debug(f"Event: {event}")
                
                # Check for on_chain_stream events which contain intermediate outputs
                if event["event"] == "on_chain_stream":
                    node_name = event.get("name", "")
                    data = event.get("data", {})
                    if "chunk" in data:
                        chunk = data["chunk"]
                        if "messages" in chunk and chunk["messages"]:
                            print(f"Streaming chunk from node '{node_name}':", chunk)
                            # Skip messages from the reflection node
                            if node_name == NodeStates.REFLECTION:
                                logger.info(f"Skipping messages from reflection node")
                                continue
                            # Yield all messages from this chunk
                            for message in chunk["messages"]:
                                if isinstance(message, AIMessage) and message.content:
                                    # Use content to deduplicate
                                    content = message.content.strip()
                                    if content in seen_contents:
                                        logger.info(f"Skipping duplicate content from '{node_name}': {content}")
                                        continue
                                    seen_contents.add(content)
                                    logger.info(f"Yielding message from '{node_name}': {content}")
                                    yield message.content

        except ValueError as ve:
            logger.error(f"ValueError in streaming_serve method: {ve}")
            raise ValueError(str(ve))
        except Exception as e:
            logger.error(f"Error in streaming_serve method: {e}")
            raise Exception(str(e))
