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
from ioa_observe.sdk.decorators import agent, graph

from agents.supervisors.logistics.graph.tools import (
    create_order,
    create_order_streaming
)
from common.llm import get_llm

logger = logging.getLogger("lungo.logistics.supervisor.graph")

class NodeStates:
    ORDERS = "orders_broker"
    ORDERS_STREAMING = "orders_broker_streaming"

class GraphState(MessagesState):
    """
    Represents the state of our graph, passed between nodes.
    """
    next_node: str
    use_streaming: bool = False

@agent(name="logistic_agent")
class LogisticGraph:
    def __init__(self):
        self.graph = self.build_graph()

    @graph(name="logistic_graph")
    def build_graph(self) -> CompiledStateGraph:
        """
        Constructs and compiles a LangGraph instance.

        Agent Flow:

        orders_broker
            - Handles coffee order requests by extracting parameters from user input
            - Directly calls create_order function to broadcast orders to logistics agents
            - Formats and returns order status updates including delivery confirmation

        orders_broker_streaming
            - Streaming version that yields order events as they arrive
            - Calls create_order_streaming to get real-time updates

        Returns:
        CompiledGraph: A fully compiled LangGraph instance ready for execution.
        """

        self.orders_llm = None

        workflow = StateGraph(GraphState)

        workflow.add_node(NodeStates.ORDERS, self._orders_node)
        workflow.add_node(NodeStates.ORDERS_STREAMING, self._orders_streaming_node)
        
        # Conditional entry point based on use_streaming flag
        def route_entry(state: GraphState):
            return NodeStates.ORDERS_STREAMING if state.get("use_streaming", False) else NodeStates.ORDERS
        
        workflow.set_conditional_entry_point(route_entry, {
            NodeStates.ORDERS: NodeStates.ORDERS,
            NodeStates.ORDERS_STREAMING: NodeStates.ORDERS_STREAMING
        })
        
        workflow.add_edge(NodeStates.ORDERS, END)
        workflow.add_edge(NodeStates.ORDERS_STREAMING, END)

        return workflow.compile()


    async def _orders_node(self, state: GraphState) -> dict:
        """
        Handles orders-related queries by directly calling the create_order function.
        """
        if not self.orders_llm:
            self.orders_llm = get_llm()

        # Get latest HumanMessage
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        if not user_msg:
            return {"messages": [AIMessage(content="No user message found.")]}

        user_query = user_msg.content.lower()
        logger.info(f"Processing order query: {user_query}")

        # Define structured output schema
        class OrderParams(BaseModel):
            farm: str = Field(description="The farm name (e.g., tatooine)")
            quantity: int = Field(description="The number of units to order")
            price: float = Field(description="The price per unit")
            has_all_params: bool = Field(description="Whether all required parameters were found in the user's request")
            missing_params: str = Field(description="Comma-separated list of missing parameters, if any")

        # Create structured output LLM (streaming=False required for structured output)
        extraction_llm = get_llm(streaming=False).with_structured_output(OrderParams, strict=True)

        sys_msg = SystemMessage(
            content="""You are an orders broker for a global coffee exchange company.
            Extract the order parameters from the user's request.
            
            Look for:
            - farm: The farm name (tatooine, brazil, colombia, vietnam, etc.)
            - quantity: The number of units to order (extract the number, ignore units like 'lbs')
            - price: The price per unit (extract the number, ignore currency symbols)
            
            Set has_all_params to true only if you found all three parameters.
            If any are missing, set has_all_params to false and list them in missing_params.
            If parameters are present, still populate them with your best guess (use empty string for farm, 0 for quantity/price if truly missing).
            """,
            pretty_repr=True,
        )

        try:
            # Extract parameters using structured output
            params = await extraction_llm.ainvoke([sys_msg, user_msg])
            logger.info(f"Extracted params: farm={params.farm}, quantity={params.quantity}, price={params.price}, has_all={params.has_all_params}")
            
            # Check if all parameters are present
            if not params.has_all_params:
                return {"messages": [AIMessage(content=f"Please provide the following information: {params.missing_params}")]}
            
            # Call the function directly
            tool_result = await create_order(farm=params.farm, quantity=params.quantity, price=params.price)
            
            # Check for errors in the result
            if "error" in str(tool_result).lower() or "failed" in str(tool_result).lower():
                error_message = f"I encountered an issue creating the order. Please try again later."
                return {"messages": [AIMessage(content=error_message)]}

            # Use LLM to format the response
            format_prompt = PromptTemplate(
                template="""You are an orders broker for a global coffee exchange company.
                The user requested to create an order.
                
                User's request: {user_message}
                
                Order result:
                {tool_result}
                
                FINAL DELIVERY HANDLING:
                If the order result contains the exact token 'DELIVERED' (indicates the order was fully delivered), 
                respond ONLY with a multiline plain text summary in the following format without any newline character (and nothing else):
                   Order <extract UUID from create_order function result> from <farm (Title Case) or unknown> for <quantity or unknown> units at <price or unknown> has been successfully delivered.
                   - Extract the UUID/order ID from the tool_result text (look for hex strings or UUID patterns).
                   - Infer farm / quantity / price from prior messages; if missing use 'unknown'.
                
                Otherwise, provide a clear and concise response to the user based on the order result.
                """,
                input_variables=["user_message", "tool_result"]
            )

            format_chain = format_prompt | self.orders_llm
            final_response = await format_chain.ainvoke({
                "user_message": user_msg.content,
                "tool_result": tool_result,
            })

            return {"messages": [AIMessage(content=final_response.content)]}

        except Exception as e:
            logger.error(f"Error in orders node: {e}")
            error_message = f"I encountered an issue creating the order: {str(e)}"
            return {"messages": [AIMessage(content=error_message)]}

    async def _orders_streaming_node(self, state: GraphState):
        """
        Streaming orders node that yields real-time order status updates as they arrive from logistics agents.
        
        This node:
        1. Extracts order parameters (farm, quantity, price) from user input using LLM structured output
        2. Calls create_order_streaming() which yields events as agents process the order
        3. Yields each order event immediately (RECEIVED_ORDER, HANDOVER_TO_SHIPPER, CUSTOMS_CLEARANCE, etc.)
        4. Accumulates all responses to detect when order is DELIVERED
        5. Uses LLM to generate a final formatted summary message when delivery is complete
        
        Flow:
        - User message -> LLM extraction -> create_order_streaming() -> Yield events in real-time -> 
          Final LLM summary (if delivered)
        
        Event Format:
        Each yielded event is a dict with: order_id, sender, receiver, message, state, timestamp
        
        Args:
            state: GraphState containing messages and routing information
            
        Yields:
            dict: State updates with AIMessage containing either:
                  - Individual order event dicts (during processing)
                  - Final formatted delivery message string (at completion)
        """
        # Extract the latest user message from the conversation history
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        if not user_msg:
            yield {"messages": [AIMessage(content="No user message found.")]}
            return

        logger.info(f"Processing order query: {user_msg.content}")

        # Define structured output schema
        class OrderParams(BaseModel):
            farm: str = Field(description="The farm name (e.g., tatooine)")
            quantity: int = Field(description="The number of units to order")
            price: float = Field(description="The price per unit")
            has_all_params: bool = Field(description="Whether all required parameters were found in the user's request")
            missing_params: str = Field(description="Comma-separated list of missing parameters, if any")

        # Create structured output LLM (streaming=False required for structured output)
        extraction_llm = get_llm(streaming=False).with_structured_output(OrderParams, strict=True)

        sys_msg = SystemMessage(
            content="""You are an orders broker for a global coffee exchange company.
            Extract the order parameters from the user's request.
            
            Look for:
            - farm: The farm name (tatooine, brazil, colombia, vietnam, etc.)
            - quantity: The number of units to order (extract the number, ignore units like 'lbs')
            - price: The price per unit (extract the number, ignore currency symbols)
            
            Set has_all_params to true only if you found all three parameters.
            If any are missing, set has_all_params to false and list them in missing_params.
            If parameters are present, still populate them with your best guess (use empty string for farm, 0 for quantity/price if truly missing).
            """,
            pretty_repr=True,
        )

        try:
            # Extract parameters using structured output
            params = await extraction_llm.ainvoke([sys_msg, user_msg])
            logger.info(f"Extracted params: farm={params.farm}, quantity={params.quantity}, price={params.price}, has_all={params.has_all_params}")
            
            # Check if all parameters are present
            if not params.has_all_params:
                yield {"messages": [AIMessage(content=f"Please provide the following information: {params.missing_params}")]}
                return
            
            farm = params.farm
            quantity = params.quantity
            price = params.price

            # Accumulate all responses and track if delivered
            all_responses = []
            delivered = False
            order_id = None
            
            # Stream responses from create_order_streaming and yield each one
            async for response in create_order_streaming(farm=farm, quantity=quantity, price=price):
                logger.info(f"Received streaming response: {response}")
                all_responses.append(response)
                
                # Check if this is a delivered status
                if isinstance(response, dict):
                    if response.get("state") == "DELIVERED":
                        delivered = True
                        order_id = response.get("order_id")
                
                # Yield each response as it arrives for streaming
                yield {"messages": [AIMessage(content=str(response))]}
            
            # If delivered, generate final formatted message using LLM
            if delivered and all_responses:
                if not self.orders_llm:
                    self.orders_llm = get_llm()
                
                format_prompt = PromptTemplate(
                    template="""You are an orders broker for a global coffee exchange company.
                    An order has been successfully delivered. Create a concise summary message.
                    
                    Order details:
                    - Order ID: {order_id}
                    - Farm: {farm}
                    - Quantity: {quantity}
                    - Price: {price}
                    
                    Respond with ONLY a single sentence in this exact format (no extra text):
                    Order {order_id} from {farm} for {quantity} units at ${price} has been successfully delivered.
                    
                    """,
                    input_variables=["order_id", "farm", "quantity", "price"]
                )
                
                format_chain = format_prompt | self.orders_llm
                final_response = await format_chain.ainvoke({
                    "order_id": order_id or "unknown",
                    "farm": farm.title(),
                    "quantity": quantity,
                    "price": f"{price:.2f}",
                })
                
                # Yield the final formatted message
                yield {"messages": [AIMessage(content=final_response.content.strip())]}

        except Exception as e:
            logger.error(f"Error in orders node: {e}")
            error_message = f"I encountered an issue creating the order: {str(e)}"
            yield {"messages": [AIMessage(content=error_message)]}

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
        Streams real-time order processing events using LangGraph's astream_events API.
        
        This method enables progressive delivery of order status updates by:
        1. Setting use_streaming=True flag to route to _orders_streaming_node
        2. Using LangGraph's astream_events() to capture node outputs as they're generated
        3. Filtering for "on_chain_stream" events which contain intermediate results
        4. Yielding AIMessage content as it arrives (order events and final summary)
        
        Flow:
        - Prompt -> Graph with use_streaming=True -> _orders_streaming_node -> 
          Stream events via astream_events() -> Filter -> Yield to caller
        
        Event Types Captured:
        - on_chain_stream: Intermediate outputs from nodes (what we yield)
        - on_chain_start/end: Node lifecycle events (logged but not yielded)
        
        Output Format:
        Yields AIMessage content which can be:
        - Order event dicts: {"order_id": "...", "sender": "...", "state": "...", ...}
        - Final summary string: "Order X from Y for Z units at $W has been successfully delivered."

        Args:
            prompt (str): User's order request (e.g., "I want to order 5000 lbs of coffee for $3.52")

        Yields:
            str or dict: Message content chunks as they arrive from the streaming node.
                        Can be order event dicts or formatted summary strings.

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
            # Set use_streaming flag to route to streaming node
            state = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "use_streaming": True
            }

            # Track seen content to prevent duplicate yields when nodes produce the same output
            seen_contents = set()

            # Stream events from the graph using astream_events (LangGraph v2 API)
            # This provides fine-grained control over streaming, emitting events for:
            # - Node starts/ends (on_chain_start, on_chain_end)
            # - Intermediate outputs (on_chain_stream)
            async for event in self.graph.astream_events(state, {"configurable": {"thread_id": uuid.uuid4()}},
                                                         version="v2"):
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
