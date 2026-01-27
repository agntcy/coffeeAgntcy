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
from ioa_observe.sdk.decorators import agent, graph

from agents.supervisors.auction.graph.tools import (
    get_farm_yield_inventory,
    get_all_farms_yield_inventory_streaming,
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
            - Respond with 'orders' if the message includes:
                * Quantity specifications (e.g., "50 lb", "100 kg")
                * Price or cost information (e.g., "for $X", "at Y cents per lb")
                * Purchase intent keywords (e.g., "need", "want", "buy", "order", "purchase")
            - Respond with 'inventory_single_farm' if the user asks about a SPECIFIC farm (Brazil, Colombia, or Vietnam)
            - Respond with 'inventory_all_farms' if the user asks about inventory/yield from ALL farms or doesn't specify a farm
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
            
            # create a structured output LLM for reflection (streaming=False required for structured output)
            self.reflection_llm = get_llm(streaming=False).with_structured_output(ShouldContinue, strict=True)

        sys_msg_reflection = SystemMessage(
            content="""You are an AI assistant reflecting on a conversation to determine if the user's request has been fully addressed.
            Review the entire conversation history provided.

            Decide whether the user's *original query* has been satisfied by the responses given so far. If the prompt is related to order, please ensure the farm information is included in the final response.
            For permission issues regarding creating a payment or list transaction, please include which operation failed in the final response.
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
          [sys_msg_reflection] + state["messages"],
          
        )
        logging.info(f"Reflection agent response: {response}")

        # Handle case where structured output returns None (can happen with streaming enabled)
        if response is None:
            logging.warning("Reflection agent returned None, defaulting to not continue")
            return {"next_node": END}

        is_duplicate_message = (
          len(state["messages"]) > 2 and state["messages"][-1].content == state["messages"][-3].content
        )
        
        should_continue = response.should_continue and not is_duplicate_message
        next_node = NodeStates.SUPERVISOR if should_continue else END

        if next_node == END and any(keyword in response.reason.lower() for keyword in ["auth", "access", "permission", "identity"]):

            err_msg = "Authentication or authorization failed. Please check your credentials and try again."
            for farm in ['colombia', 'brazil', 'vietnam']:
                if farm in state["messages"][-1].content.lower():
                    err_msg = f"The supervisor agent doesn't have permission to access the {farm.title()} farm. Please verify your access credentials and try again."
                    break

            for keyword in ["transaction", "payment"]:
                if keyword in state["messages"][-1].content.lower():
                    err_msg = f"Not authorized to perform '{keyword}' operation through the Payment MCP service. Please verify your farm credentials and try again."
                    break

            return {
                "next_node": END,
                "messages": [AIMessage(content=err_msg)],
            }

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

    async def _inventory_all_farms_node(self, state: GraphState) -> dict:
        """
        Handles inventory queries for all farms by streaming data from multiple farm agents.
        
        Behavior:
        - Streaming mode (astream_events): Yields each chunk as it arrives from farms,
          allowing progressive display of inventory data in real-time.
        - Non-streaming mode (ainvoke): Only the final aggregated response is used,
          containing the complete inventory from all farms.
        """
        # Extract the latest user message from the conversation state
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        if not user_msg:
            yield {"messages": [AIMessage(content="No user message found.")]}

        logger.info(f"Processing all farms inventory query: {user_msg.content}")

        try:
            # Collect inventory data from all farms via streaming
            full_response = ""
            success_count = 0
            error_count = 0
            has_timeout_warning = False
            
            async for chunk in get_all_farms_yield_inventory_streaming(user_msg.content):
                # Yield each chunk immediately for streaming mode
                # In non-streaming mode, these intermediate yields are ignored
                yield {"messages": [AIMessage(content=chunk.strip())]}
                full_response += chunk
                
                # Track successful responses vs errors from the streaming tool
                if chunk.strip().startswith("Error"):
                    error_count += 1
                elif "timeout" in chunk.lower() or "timed out" in chunk.lower():
                    has_timeout_warning = True
                else:
                    success_count += 1
            
            # Check if we received any successful responses
            if success_count == 0:
                error_message = "No responses received from any farms. Please ensure farm agents are running and try again."
                logger.warning(error_message)
                yield {"messages": [AIMessage(content=error_message)]}
                return
            
            # Yield final aggregated response with complete inventory
            # This is what gets returned in non-streaming mode (ainvoke)
            # In streaming mode, this provides the final summary with all data
            final_content = f"Here is the current coffee yield inventory from the farms:\n\n{full_response.strip()}"
            
            # Add note if there were errors or timeout warnings
            if error_count > 0 or has_timeout_warning:
                final_content += f"\n\nNote: Some farms encountered errors or did not respond in time. Showing available inventory data."
                logger.warning(f"Partial farm responses: {success_count} successful, {error_count} errors")
            
            yield {"messages": [AIMessage(content=final_content)], "full_response": final_content}

        except Exception as e:
            logger.error(f"Error in all farms inventory node: {e}")
            error_message = f"I encountered an issue retrieving information from the farms: {str(e)}. Please ensure all farm agents are running and try again."
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

        auth_failure = ""
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

                    if "auth" in result_str.lower():
                        auth_failure = result_str
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
            1.  **Process ALL tool results provided in the context.** This includes both successful and failed attempts. If the context contains error messages related to authentication or authorization, please note them specifically.
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
                "I'm sorry, I was unable to complete your order request for all items. "
                "An issue occurred for some parts. Please try again later."
            )

            if auth_failure:
                forced_error_message = f"{auth_failure} Please try again later."

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

    async def serve(self, prompt: str) -> str:
        """
        Processes the input prompt and returns a complete response from the graph execution.
        
        This method uses LangGraph's ainvoke() to execute the entire graph synchronously,
        waiting for all nodes to complete before returning the final result. Unlike streaming_serve(),
        this method blocks until the full execution is complete and returns only the final output.

        Args:
            prompt (str): The input prompt to be processed by the graph.

        Returns:
            str: The final response content from the last AIMessage in the graph execution.

        Raises:
            ValueError: If the prompt is empty or not a string.
            RuntimeError: If no valid AIMessage is found in the graph response.
            Exception: If any error occurs during graph execution.
        """
        try:
            logger.debug(f"Received prompt: {prompt}")
            
            # Validate input prompt
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("Prompt must be a non-empty string.")
            
            # Execute the graph using ainvoke() - this runs the entire graph to completion
            # The graph will route through nodes based on the routing logic and return the final state
            result = await self.graph.ainvoke({
                "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
                ],
            }, {"configurable": {"thread_id": uuid.uuid4()}})

            # Extract messages from the final state
            # The messages list contains the full conversation history including user, AI, and tool messages
            messages = result.get("messages", [])
            if not messages:
                raise RuntimeError("No messages found in the graph response.")

            # Find the last AIMessage with non-empty content
            # We iterate in reverse to get the most recent response from the agent
            # This skips over any tool messages or empty responses
            for message in reversed(messages):
                if isinstance(message, AIMessage) and message.content.strip():
                    logger.debug(f"Valid AIMessage found: {message.content.strip()}")
                    return message.content.strip()

            # If no valid AIMessage is found, raise an error
            raise RuntimeError("No valid AIMessage found in the graph response.")
        except ValueError as ve:
            logger.error(f"ValueError in serve method: {ve}")
            raise ValueError(str(ve))
        except Exception as e:
            logger.error(f"Error in serve method: {e}")
            raise Exception(str(e))

    async def streaming_serve(self, prompt: str):
        """
        Streams the graph execution using LangGraph's astream_events API, yielding chunks as they arrive.
        
        This method leverages LangGraph's event streaming to provide real-time updates as the graph
        executes across multiple nodes. It captures intermediate outputs from each node and streams
        them back to the caller, enabling progressive data delivery for long-running operations.

        LangGraph Reference:
            - Uses `astream_events()` for streaming
            - Each event includes metadata (node name, event type) and data (chunks, messages)

        Args:
            prompt (str): The input prompt to be processed by the graph.

        Yields:
            str: Message content chunks as they arrive from nodes during graph execution.
                 Only yields AIMessage content, filtering out duplicates and reflection nodes.

        Raises:
            ValueError: If the prompt is empty or not a string.
            Exception: If any error occurs during graph execution or streaming.
        """
        try:
            logger.debug(f"Received streaming prompt: {prompt}")
            
            # Validate input prompt
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("Prompt must be a non-empty string.")

            # Construct the initial state for the LangGraph execution
            # The state follows the MessageGraph pattern with a messages list
            state = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            }

            # Track seen content to prevent duplicate yields when nodes produce the same output
            seen_contents = set()
            
            # Stream events from the graph using astream_events (LangGraph v2 API)
            # This provides fine-grained control over streaming, emitting events for:
            # - Node starts/ends (on_chain_start, on_chain_end)
            # - Intermediate outputs (on_chain_stream)
            async for event in self.graph.astream_events(state, {"configurable": {"thread_id": uuid.uuid4()}}, version="v2"):
                logger.debug(f"Event: {event}")
                
                # Filter for "on_chain_stream" events which contain intermediate node outputs
                # These events fire when a node produces output during execution, allowing
                # us to stream results progressively rather than waiting for full completion
                if event["event"] == "on_chain_stream":
                    node_name = event.get("name", "")
                    data = event.get("data", {})
                    
                    # Extract the chunk from the event data
                    # Chunks contain partial state updates from the executing node
                    if "chunk" in data:
                        chunk = data["chunk"]
                        
                        # Check if this chunk contains messages (the primary output type)
                        if "messages" in chunk and chunk["messages"]:
                            logger.info(f"Streaming chunk from node '{node_name}': {chunk}")
                            
                            # Skip messages from the reflection node to avoid streaming internal reasoning
                            # The reflection node performs self-evaluation and shouldn't be user-facing
                            if node_name == NodeStates.REFLECTION:
                                logger.info(f"Skipping messages from reflection node")
                                continue
                            
                            # Process and yield all messages from this chunk
                            for message in chunk["messages"]:
                                # Only yield AIMessage content (responses from the agent/LLM)
                                # Filter out system messages, tool messages, and human messages
                                if isinstance(message, AIMessage) and message.content:
                                    content = message.content.strip()
                                    
                                    # Deduplicate: Skip if we've already yielded this exact content
                                    if content in seen_contents:
                                        logger.info(f"Skipping duplicate content from '{node_name}': {content}")
                                        continue
                                    
                                    # Mark this content as seen and yield it to the caller
                                    seen_contents.add(content)
                                    logger.info(f"Yielding message from '{node_name}': {content}")
                                    yield message.content

        except ValueError as ve:
            logger.error(f"ValueError in streaming_serve method: {ve}")
            raise ValueError(str(ve))
        except Exception as e:
            logger.error(f"Error in streaming_serve method: {e}")
            raise Exception(str(e))
