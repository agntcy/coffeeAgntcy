# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Human-in-the-Loop Exchange Graph
=================================

This module extends the Exchange Graph with human-in-the-loop capabilities using
LangGraph's interrupt() function for pausing execution during human intervention.

Purpose:
    Enable human oversight for high-stakes order decisions by pausing graph
    execution, presenting options to the user, and resuming with their selection.

Graph Flow:
    1. User query → SUPERVISOR routes to appropriate handler
    2. For orders: ORDERS node gathers context
    3. TRIGGER_EVALUATION runs WHEN-TO-TRIGGER model
    4. If triggered (confidence >= threshold):
       - RESPONSE_GENERATION runs WHAT-TO-RESPOND model
       - HUMAN_INTERVENTION calls interrupt() with scenario options
       - Graph pauses, control returns to caller
       - On resume: PROCESS_HUMAN_DECISION handles selection
    5. REFLECTION determines if conversation is complete

Graph Structure:
    SUPERVISOR
        ├── INVENTORY_SINGLE_FARM → REFLECTION → END
        ├── INVENTORY_ALL_FARMS → REFLECTION → END
        ├── ORDERS → TRIGGER_EVALUATION
        │              ├── [TRIGGER] → RESPONSE_GENERATION → HUMAN_INTERVENTION
        │              │                                          ↓
        │              │                              PROCESS_HUMAN_DECISION → END
        │              └── [NO_TRIGGER] → ORDERS_TOOLS → REFLECTION → END
        └── GENERAL_INFO → END

Example Usage:
    >>> from agents.supervisors.auction.graph.graph_hitl import ExchangeGraphHITL
    >>> 
    >>> # Initialize the graph
    >>> graph = ExchangeGraphHITL(enable_hitl=True)
    >>> 
    >>> # Start a request (may interrupt for human input)
    >>> result = await graph.serve("500 lbs, budget $2000")
    >>> 
    >>> if result.get("status") == "awaiting_human_input":
    >>>     # Present options to user, get their selection
    >>>     user_choice = "Balanced Diversification"
    >>>     final_result = await graph.resume(result["thread_id"], user_choice)

Reference: https://docs.langchain.com/oss/python/langgraph/interrupts
"""

import logging
import uuid
from typing import Optional, Dict, Any, Literal

from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import MessagesState, StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from ioa_observe.sdk.decorators import agent, graph

from agents.supervisors.auction.graph.tools import (
    get_farm_yield_inventory,
    get_all_farms_yield_inventory_streaming,
    create_order,
    get_order_details,
    tools_or_next
)
from agents.supervisors.auction.graph.hitl import (
    get_trigger_model,
    get_respond_model,
    TriggerDecision,
    TriggerModelOutput,
)
from common.llm import get_llm

logger = logging.getLogger("lungo.supervisor.graph_hitl")

class NodeStates:
    """
    Node state identifiers for the graph.
    
    These constants define the node names used in the LangGraph workflow.
    Using a class with constants ensures consistent naming across the codebase.
    """
    SUPERVISOR = "exchange_supervisor"
    
    INVENTORY_SINGLE_FARM = "inventory_single_farm"
    INVENTORY_ALL_FARMS = "inventory_all_farms"
    
    ORDERS = "orders_broker"
    ORDERS_TOOLS = "orders_tools"

    # HITL nodes
    TRIGGER_EVALUATION = "trigger_evaluation"
    RESPONSE_GENERATION = "response_generation"
    HUMAN_INTERVENTION = "human_intervention"
    PROCESS_HUMAN_DECISION = "process_human_decision"
    
    REFLECTION = "reflection"
    GENERAL_INFO = "general"


class HITLGraphState(MessagesState):
    """
    Extended state for the HITL-enabled graph.
    
    Includes standard messaging state plus HITL-specific fields.
    """
    next_node: str = ""
    full_response: str = ""
    
    # HITL state
    hitl_enabled: bool = True
    trigger_result: Optional[Dict[str, Any]] = None  # Output from WHEN-TO-TRIGGER model
    intervention_options: Optional[Dict[str, Any]] = None  # Output from WHAT-TO-RESPOND model
    human_decision: Optional[str] = None
    selected_scenario: Optional[str] = None
    awaiting_human_input: bool = False


@agent(name="exchange_agent_hitl")
class ExchangeGraphHITL:
    """
    Exchange Graph with Human-in-the-Loop capabilities.
    
    This graph uses LangGraph's interrupt() function to pause execution
    when human intervention is needed, surfacing options to the caller
    and resuming with the human's decision.
    """
    
    def __init__(self, enable_hitl: bool = True):
        """
        Initialize the HITL-enabled Exchange Graph.
        
        Args:
            enable_hitl: Whether to enable human-in-the-loop functionality.
                        If False, behaves like the standard ExchangeGraph.
        """
        self.enable_hitl = enable_hitl
        self.trigger_model = get_trigger_model()
        self.respond_model = get_respond_model()
        
        # LLMs (lazy initialization)
        self.supervisor_llm = None
        self.reflection_llm = None
        self.orders_llm = None
        
        # Checkpointer for interrupt persistence
        # In production, use a durable checkpointer (PostgresSaver, etc.)
        self.checkpointer = MemorySaver()
        
        # Build the graph
        self.graph = self.build_graph()
        
        logger.info(f"ExchangeGraphHITL initialized with HITL={enable_hitl}")
    
    @graph(name="exchange_graph_hitl")
    def build_graph(self) -> CompiledStateGraph:
        """
        Build the HITL-enabled exchange graph.
        
        Graph Structure:
        
        SUPERVISOR
            ├── INVENTORY_SINGLE_FARM → REFLECTION
            ├── INVENTORY_ALL_FARMS → REFLECTION
            ├── ORDERS → TRIGGER_EVALUATION
            │              ├── [TRIGGER] → RESPONSE_GENERATION → HUMAN_INTERVENTION
            │              │                                          ↓
            │              │                              PROCESS_HUMAN_DECISION → ORDERS_TOOLS
            │              └── [NO_TRIGGER] → ORDERS_TOOLS
            └── GENERAL_INFO → END
        
        REFLECTION
            ├── [continue] → SUPERVISOR
            └── [end] → END
        """
        workflow = StateGraph(HITLGraphState)
        
        # === Define Nodes ===
        
        # Standard nodes
        workflow.add_node(NodeStates.SUPERVISOR, self._supervisor_node)
        workflow.add_node(NodeStates.INVENTORY_SINGLE_FARM, self._inventory_single_farm_node)
        workflow.add_node(NodeStates.INVENTORY_ALL_FARMS, self._inventory_all_farms_node)
        workflow.add_node(NodeStates.ORDERS, self._orders_node)
        workflow.add_node(NodeStates.ORDERS_TOOLS, ToolNode([create_order, get_order_details]))
        workflow.add_node(NodeStates.REFLECTION, self._reflection_node)
        workflow.add_node(NodeStates.GENERAL_INFO, self._general_response_node)
        
        # HITL nodes
        workflow.add_node(NodeStates.TRIGGER_EVALUATION, self._trigger_evaluation_node)
        workflow.add_node(NodeStates.RESPONSE_GENERATION, self._response_generation_node)
        workflow.add_node(NodeStates.HUMAN_INTERVENTION, self._human_intervention_node)
        workflow.add_node(NodeStates.PROCESS_HUMAN_DECISION, self._process_human_decision_node)
        
        # === Define Edges ===
        
        workflow.set_entry_point(NodeStates.SUPERVISOR)
        
        # Supervisor routes to appropriate node
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
        
        # Inventory nodes → Reflection
        workflow.add_edge(NodeStates.INVENTORY_SINGLE_FARM, NodeStates.REFLECTION)
        workflow.add_edge(NodeStates.INVENTORY_ALL_FARMS, NodeStates.REFLECTION)
        
        # Orders → Trigger Evaluation (when HITL enabled)
        # The orders node now prepares context, then goes to trigger evaluation
        workflow.add_edge(NodeStates.ORDERS, NodeStates.TRIGGER_EVALUATION)
        
        # Trigger Evaluation routes based on WHEN-TO-TRIGGER decision
        workflow.add_conditional_edges(
            NodeStates.TRIGGER_EVALUATION,
            self._route_from_trigger,
            {
                NodeStates.RESPONSE_GENERATION: NodeStates.RESPONSE_GENERATION,
                NodeStates.ORDERS_TOOLS: NodeStates.ORDERS_TOOLS,
            },
        )
        
        # Response Generation → Human Intervention
        workflow.add_edge(NodeStates.RESPONSE_GENERATION, NodeStates.HUMAN_INTERVENTION)
        
        # Human Intervention → Process Human Decision
        workflow.add_edge(NodeStates.HUMAN_INTERVENTION, NodeStates.PROCESS_HUMAN_DECISION)
        
        # Process Human Decision → Orders Tools (to execute the order)
        workflow.add_edge(NodeStates.PROCESS_HUMAN_DECISION, NodeStates.ORDERS_TOOLS)
        
        # Orders Tools → Reflection
        workflow.add_edge(NodeStates.ORDERS_TOOLS, NodeStates.REFLECTION)
        
        # General Info → END
        workflow.add_edge(NodeStates.GENERAL_INFO, END)
        
        # Reflection routes
        workflow.add_conditional_edges(
            NodeStates.REFLECTION,
            lambda state: state.get("next_node", END),
            {
                NodeStates.SUPERVISOR: NodeStates.SUPERVISOR,
                END: END,
            },
        )
        
        # Compile with checkpointer for interrupt support
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _route_from_trigger(self, state: HITLGraphState) -> str:
        """Route based on trigger evaluation result"""
        trigger_result = state.get("trigger_result")
        
        if not trigger_result or not self.enable_hitl:
            # No trigger or HITL disabled → proceed to tools
            return NodeStates.ORDERS_TOOLS
        
        if trigger_result.get("decision") == TriggerDecision.TRIGGER.value:
            # Human intervention needed
            return NodeStates.RESPONSE_GENERATION
        
        # No intervention needed
        return NodeStates.ORDERS_TOOLS
    
    # === STANDARD NODES (simplified from original) ===
    
    async def _supervisor_node(self, state: HITLGraphState) -> dict:
        """Route user message to appropriate handler"""
        if not self.supervisor_llm:
            self.supervisor_llm = get_llm()
        
        user_message = state["messages"]
        
        prompt = PromptTemplate(
            template="""You are a global coffee exchange agent connecting users to coffee farms in Brazil, Colombia, and Vietnam. 
            Based on the user's message, determine the appropriate action:
            - Respond with 'orders' if the message includes:
                * Quantity specifications (e.g., "50 lb", "100 kg", "500 lbs")
                * Price or cost information (e.g., "for $X", "budget", "capped at")
                * Purchase intent keywords (e.g., "need", "want", "buy", "order", "purchase", "Q2 order")
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
    
    async def _inventory_single_farm_node(self, state: HITLGraphState) -> Dict[str, Any]:
        """
        Handle single farm inventory queries.
        
        Extracts the farm name from the user query and retrieves inventory data.
        
        Args:
            state: Current graph state containing messages
            
        Returns:
            Dict with AIMessage containing farm inventory or error message
        """
        # Find the most recent human message
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        if not user_msg:
            logger.warning("No user message found in state for inventory query")
            return {"messages": [AIMessage(content="No user message found.")]}
        
        # Extract farm name from query
        query = user_msg.content.lower()
        farm: Optional[str] = None
        for farm_name in ["brazil", "colombia", "vietnam"]:
            if farm_name in query:
                farm = farm_name
                break
        
        if not farm:
            return {"messages": [AIMessage(content="Please specify which farm (Brazil, Colombia, or Vietnam).")]}
        
        try:
            result = await get_farm_yield_inventory(user_msg.content, farm)
            # Strip trailing whitespace to avoid Bedrock Claude error:
            # "final assistant content cannot end with trailing whitespace"
            result = result.strip() if isinstance(result, str) else str(result).strip()
            return {"messages": [AIMessage(content=f"**{farm.title()} Farm Inventory:**\n{result}")]}
        except Exception as e:
            # Log full exception with traceback for debugging
            logger.exception(f"Error querying {farm} farm: {e}")
            return {"messages": [AIMessage(content=f"Error retrieving {farm} farm data: {type(e).__name__}")]}
    
    async def _inventory_all_farms_node(self, state: HITLGraphState) -> Dict[str, Any]:
        """
        Handle queries for all farms inventory.
        
        Streams inventory data from all farms (Brazil, Colombia, Vietnam)
        and aggregates the results.
        
        Args:
            state: Current graph state containing messages
            
        Returns:
            Dict with AIMessage containing aggregated farm inventory
        """
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        if not user_msg:
            logger.warning("No user message found in state for all-farms inventory query")
            return {"messages": [AIMessage(content="No user message found.")]}
        
        try:
            # Stream responses from all farms and aggregate
            full_response = ""
            async for chunk in get_all_farms_yield_inventory_streaming(user_msg.content):
                full_response += chunk + "\n"
            
            # Strip trailing whitespace to avoid Bedrock Claude error:
            # "final assistant content cannot end with trailing whitespace"
            full_response = full_response.strip()
            return {"messages": [AIMessage(content=f"**All Farms Inventory:**\n{full_response}")]}
        except Exception as e:
            # Log full exception with traceback for debugging
            logger.exception(f"Error querying all farms: {e}")
            return {"messages": [AIMessage(content=f"Error retrieving farm data: {type(e).__name__}")]}
    
    async def _orders_node(self, state: HITLGraphState) -> dict:
        """
        Prepare order context for HITL evaluation.
        
        This node extracts order parameters from the user's message
        and prepares context for the trigger evaluation.
        """
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        if not user_msg:
            return {"messages": [AIMessage(content="No user message found.")]}
        
        logger.info(f"[ORDERS] Processing order request: {user_msg.content}")
        
        # Store the order context for trigger evaluation
        return {
            "messages": [AIMessage(content=f"Analyzing order request: {user_msg.content}")],
        }
    
    def _general_response_node(self, state: HITLGraphState) -> dict:
        """Handle general (non-order, non-inventory) queries"""
        return {
            "next_node": END,
            "messages": [AIMessage(content="I'm not sure how to handle that. Could you please clarify?")],
        }
    
    async def _reflection_node(self, state: HITLGraphState) -> dict:
        """Determine if the conversation should continue"""
        if not self.reflection_llm:
            class ShouldContinue(BaseModel):
                should_continue: bool = Field(description="Whether to continue processing")
                reason: str = Field(description="Reason for decision")
            
            self.reflection_llm = get_llm().with_structured_output(ShouldContinue, strict=True)
        
        sys_msg = SystemMessage(
            content="""You are an AI assistant determining if a user's request has been fully addressed.
            Set 'should_continue' to false if the last AI message provides a conclusive answer.
            Set 'should_continue' to true only if more information is clearly needed."""
        )
        
        response = await self.reflection_llm.ainvoke([sys_msg] + state["messages"])
        
        is_duplicate = (
            len(state["messages"]) > 2 and 
            state["messages"][-1].content == state["messages"][-3].content
        )
        
        should_continue = response.should_continue and not is_duplicate
        next_node = NodeStates.SUPERVISOR if should_continue else END
        
        return {"next_node": next_node}
    
    # === HITL NODES ===
    
    async def _trigger_evaluation_node(self, state: HITLGraphState) -> dict:
        """
        WHEN-TO-TRIGGER MODEL (Small Language Model)
        
        Runs inference on the WHEN-TO-TRIGGER model to decide if human
        intervention is needed.
        
        Input: Raw user query (no preprocessing needed)
        Output: Decision (TRIGGER/NO_TRIGGER), confidence score, reasons
        """
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        if not user_msg:
            return {"trigger_result": None}
        
        logger.info(f"[TRIGGER_EVALUATION] Running WHEN-TO-TRIGGER model on: {user_msg.content}")
        
        # Run the WHEN-TO-TRIGGER model inference
        # Model takes raw user query directly
        trigger_output = self.trigger_model.inference(user_query=user_msg.content)
        
        # Add a message about the evaluation
        if trigger_output.decision == TriggerDecision.TRIGGER:
            msg = f"🔔 **Human Review Required** (Confidence: {trigger_output.confidence:.0%})\n\nReasons:\n"
            msg += "\n".join(f"- {r}" for r in trigger_output.reasons)
        else:
            msg = "✅ Proceeding with standard order processing..."
        
        return {
            "trigger_result": trigger_output.to_dict(),
            "messages": [AIMessage(content=msg)],
        }
    
    async def _response_generation_node(self, state: HITLGraphState) -> dict:
        """
        WHAT-TO-RESPOND MODEL (Small Language Model)
        
        Runs inference on the WHAT-TO-RESPOND model to generate
        options and scenarios for human review.
        
        Input: User query + trigger output
        Output: Scenarios, recommendation, rationale
        """
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        trigger_result_dict = state.get("trigger_result", {})
        
        logger.info("[RESPONSE_GENERATION] Running WHAT-TO-RESPOND model...")
        
        # Reconstruct trigger output from state
        trigger_output = TriggerModelOutput(
            decision=TriggerDecision(trigger_result_dict.get("decision", "NO_TRIGGER")),
            confidence=trigger_result_dict.get("confidence", 0),
            reasons=trigger_result_dict.get("reasons", []),
            raw_output=trigger_result_dict.get("raw_output"),
        )
        
        # Run the WHAT-TO-RESPOND model inference
        # Model takes user query and trigger output directly
        options = self.respond_model.inference(
            user_query=user_msg.content if user_msg else "",
            trigger_output=trigger_output,
            inventory_data=None,  # Would be actual inventory in production
        )
        
        return {
            "intervention_options": options.to_dict(),
            "messages": [AIMessage(content=options.summary)],
        }
    
    async def _human_intervention_node(self, state: HITLGraphState) -> dict:
        """
        HUMAN INTERVENTION NODE
        
        Uses LangGraph's interrupt() to pause execution and surface
        options to the human. Execution resumes when the human responds
        with their decision.
        
        Reference: https://docs.langchain.com/oss/python/langgraph/interrupts
        """
        options = state.get("intervention_options", {})
        trigger_result = state.get("trigger_result", {})
        
        logger.info("[HUMAN_INTERVENTION] Pausing for human input")
        
        # Build the interrupt payload with explicit model information
        interrupt_payload = {
            "type": "human_intervention_required",
            
            # Model 1: When-to-Trigger Model output
            "trigger_model": {
                "name": "When-to-Trigger Model",
                "description": "Analyzes user request to determine if human review is needed",
                "decision": trigger_result.get("decision", "TRIGGER"),
                "confidence": trigger_result.get("confidence", 0),
                "reasons": trigger_result.get("reasons", []),
            },
            
            # Model 2: How-to-Respond Model output
            "respond_model": {
                "name": "How-to-Respond Model",
                "description": "Generates options and scenarios for human selection",
                "summary": options.get("summary", ""),
                "scenarios": options.get("scenarios", []),
                "recommendation": options.get("recommendation", ""),
                "rationale": options.get("rationale", ""),
            },
            
            # Legacy fields for backwards compatibility
            "summary": options.get("summary", ""),
            "scenarios": options.get("scenarios", []),
            "recommendation": options.get("recommendation", ""),
            "rationale": options.get("rationale", ""),
            "instructions": "Please select one of the options below.",
        }
        
        # === INTERRUPT EXECUTION ===
        # This pauses the graph and surfaces interrupt_payload to the caller.
        # When resumed with Command(resume=...), the resume value becomes
        # the return value of this interrupt() call.
        human_response = interrupt(interrupt_payload)
        
        logger.info(f"[HUMAN_INTERVENTION] Received human response: {human_response}")
        
        # Parse the human's response
        return {
            "human_decision": human_response,
            "awaiting_human_input": False,
            "messages": [HumanMessage(content=f"Human selected: {human_response}")],
        }
    
    async def _process_human_decision_node(self, state: HITLGraphState) -> dict:
        """
        Process the human's decision and execute the selected option.
        
        This is a GENERIC handler that works with any type of HITL scenario.
        It dynamically formats the response based on whatever fields are
        present in the selected scenario.
        
        The response is built entirely from:
        - The scenario name and description
        - Any key-value pairs in the scenario (displayed generically)
        - The original user query for context
        """
        human_decision = state.get("human_decision", "")
        options = state.get("intervention_options", {})
        scenarios = options.get("scenarios", [])
        
        # Get original user message for context
        user_msg = next((m for m in state["messages"] if m.type == "human"), None)
        original_query = user_msg.content if user_msg else "your request"
        
        logger.info(f"[PROCESS_DECISION] Processing human decision: {human_decision}")
        
        # Find the selected scenario
        selected_scenario = None
        for scenario in scenarios:
            if scenario.get("name", "").lower() in human_decision.lower():
                selected_scenario = scenario
                break
        
        if selected_scenario:
            scenario_name = selected_scenario.get("name", "Selected Option")
            description = selected_scenario.get("description", "")
            
            # Build clean, professional response
            response = f"**Selection Confirmed**\n\n"
            response += f"Option: {scenario_name}\n"
            
            if description:
                response += f"Strategy: {description}\n"
            
            response += "\n"
            
            # Dynamically display all scenario fields (except name/description)
            for key, value in selected_scenario.items():
                if key in ("name", "description"):
                    continue
                
                # Format the key nicely
                display_key = key.replace("_", " ").title()
                
                # Format value based on type
                if isinstance(value, dict):
                    # Handle nested dicts (like allocations)
                    if value:
                        response += f"{display_key}:\n"
                        for sub_key, sub_value in value.items():
                            sub_display = sub_key.replace("_", " ").title()
                            response += f"  - {sub_display}: {self._format_value(sub_value)}\n"
                elif isinstance(value, list):
                    # Handle lists
                    if value:
                        response += f"{display_key}: {', '.join(str(v) for v in value)}\n"
                elif value is not None and value != "":
                    response += f"{display_key}: {self._format_value(value)}\n"
            
            response += "\n---\n\n"
            response += f"Status: Completed\n"
            response += f"Your selection has been processed successfully."
            
            return {
                "selected_scenario": scenario_name,
                "status": "completed",
                "scenario_data": selected_scenario,
                "messages": [AIMessage(content=response)],
            }
        else:
            # Human provided custom instructions (not matching any scenario)
            return {
                "human_decision": human_decision,
                "status": "custom_processing",
                "messages": [AIMessage(content=f"**Processing Custom Input**\n\nInput received: {human_decision}\n\nStatus: Processing your request...")],
            }
    
    def _format_value(self, value) -> str:
        """Format a value for display in the response."""
        if isinstance(value, float):
            if value >= 100 and value == int(value):
                return f"{int(value):,}"
            elif value >= 1:
                return f"{value:,.2f}"
            else:
                return f"{value:.0%}" if value < 1 else str(value)
        elif isinstance(value, int):
            return f"{value:,}"
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        else:
            return str(value)
    
    # === SERVE METHODS ===
    
    async def serve(self, prompt: str, thread_id: str = None) -> Dict[str, Any]:
        """
        Execute the graph and return the result.
        
        For HITL-enabled graphs, this may return an interrupt payload
        instead of a final response if human intervention is needed.
        
        Args:
            prompt: The user's input prompt
            thread_id: Optional thread ID for interrupt/resume (generated if not provided)
        
        Returns:
            Dict with either:
            - {"response": "..."} for completed requests
            - {"interrupt": {...}, "thread_id": "..."} for interrupted requests
        """
        thread_id = thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        logger.info(f"[SERVE] Processing prompt with thread_id={thread_id}")
        
        try:
            result = await self.graph.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config=config,
            )
            
            # Check if we hit an interrupt
            if "__interrupt__" in result:
                interrupt_data = result["__interrupt__"]
                logger.info(f"[SERVE] Graph interrupted: {interrupt_data}")
                return {
                    "interrupt": interrupt_data[0].value if interrupt_data else {},
                    "thread_id": thread_id,
                    "status": "awaiting_human_input",
                }
            
            # Extract final response
            messages = result.get("messages", [])
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content.strip():
                    return {"response": msg.content.strip(), "thread_id": thread_id}
            
            return {"response": "No response generated.", "thread_id": thread_id}
            
        except Exception as e:
            logger.error(f"[SERVE] Error: {e}")
            raise
    
    async def resume(self, thread_id: str, human_response: str) -> Dict[str, Any]:
        """
        Resume a paused graph with the human's response.
        
        Args:
            thread_id: The thread ID from the interrupted request
            human_response: The human's decision/selection
        
        Returns:
            Dict with the final response after resuming
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        logger.info(f"[RESUME] Resuming thread_id={thread_id} with response={human_response}")
        
        try:
            result = await self.graph.ainvoke(
                Command(resume=human_response),
                config=config,
            )
            
            # Check for another interrupt (unlikely but possible)
            if "__interrupt__" in result:
                interrupt_data = result["__interrupt__"]
                return {
                    "interrupt": interrupt_data[0].value if interrupt_data else {},
                    "thread_id": thread_id,
                    "status": "awaiting_human_input",
                }
            
            # Extract final response
            messages = result.get("messages", [])
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content.strip():
                    return {"response": msg.content.strip(), "thread_id": thread_id}
            
            return {"response": "Order processed.", "thread_id": thread_id}
            
        except Exception as e:
            logger.error(f"[RESUME] Error: {e}")
            raise
