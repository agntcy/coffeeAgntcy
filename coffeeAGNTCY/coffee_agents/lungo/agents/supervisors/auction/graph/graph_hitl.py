# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Human-in-the-Loop Exchange Graph

This module extends the Exchange Graph with human-in-the-loop capabilities using
LangGraph's interrupt() function. The flow is:

1. User query → Supervisor routes to appropriate node
2. Orders node gathers context and prepares order
3. TRIGGER_EVALUATION node runs WHEN-TO-TRIGGER model
4. If triggered:
   - RESPONSE_GENERATION node runs WHAT-TO-RESPOND model
   - HUMAN_INTERVENTION node calls interrupt() with options
   - Human reviews and responds
   - Graph resumes with human's decision
5. Continue with order execution based on human input

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
    """Node state identifiers for the graph"""
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
    
    async def _inventory_single_farm_node(self, state: HITLGraphState) -> dict:
        """Handle single farm inventory queries"""
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        if not user_msg:
            return {"messages": [AIMessage(content="No user message found.")]}
        
        query = user_msg.content.lower()
        farm = None
        for f in ["brazil", "colombia", "vietnam"]:
            if f in query:
                farm = f
                break
        
        if not farm:
            return {"messages": [AIMessage(content="Please specify which farm (Brazil, Colombia, or Vietnam).")]}
        
        try:
            result = await get_farm_yield_inventory(user_msg.content, farm)
            return {"messages": [AIMessage(content=f"**{farm.title()} Farm Inventory:**\n{result}")]}
        except Exception as e:
            logger.error(f"Error querying {farm} farm: {e}")
            return {"messages": [AIMessage(content=f"Error retrieving {farm} farm data.")]}
    
    async def _inventory_all_farms_node(self, state: HITLGraphState) -> dict:
        """Handle all farms inventory queries"""
        user_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
        if not user_msg:
            return {"messages": [AIMessage(content="No user message found.")]}
        
        try:
            full_response = ""
            async for chunk in get_all_farms_yield_inventory_streaming(user_msg.content):
                full_response += chunk + "\n"
            
            return {"messages": [AIMessage(content=f"**All Farms Inventory:**\n{full_response}")]}
        except Exception as e:
            logger.error(f"Error querying all farms: {e}")
            return {"messages": [AIMessage(content="Error retrieving farm data.")]}
    
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
        
        logger.info("[HUMAN_INTERVENTION] Pausing for human input")
        
        # Build the interrupt payload
        interrupt_payload = {
            "type": "human_intervention_required",
            "summary": options.get("summary", ""),
            "scenarios": options.get("scenarios", []),
            "recommendation": options.get("recommendation", ""),
            "rationale": options.get("rationale", ""),
            "instructions": (
                "Please select one of the scenarios below by responding with the scenario name "
                "(e.g., 'Budget-Optimized', 'Quality-First', 'Balanced Diversification', 'Budget-Strict'), "
                "or provide custom instructions."
            ),
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
        Process the human's decision and prepare for order execution.
        
        Interprets the human's selection and adjusts the order parameters
        accordingly before proceeding to the orders tools.
        """
        human_decision = state.get("human_decision", "")
        options = state.get("intervention_options", {})
        scenarios = options.get("scenarios", [])
        
        logger.info(f"[PROCESS_DECISION] Processing human decision: {human_decision}")
        
        # Find the selected scenario
        selected_scenario = None
        for scenario in scenarios:
            if scenario.get("name", "").lower() in human_decision.lower():
                selected_scenario = scenario
                break
        
        if selected_scenario:
            # Build order message based on selected scenario
            allocations = selected_scenario.get("farm_allocations", {})
            total_cost = selected_scenario.get("total_cost", 0)
            
            order_summary = f"**Executing order based on '{selected_scenario['name']}' scenario:**\n\n"
            order_summary += f"📦 **Allocations:**\n"
            for farm, qty in allocations.items():
                if qty > 0:
                    order_summary += f"- {farm.title()}: {qty} lbs\n"
            order_summary += f"\n💰 **Estimated Total:** ${total_cost:,.2f}"
            
            return {
                "selected_scenario": selected_scenario.get("name"),
                "messages": [AIMessage(content=order_summary)],
            }
        else:
            # Human provided custom instructions
            return {
                "human_decision": human_decision,
                "messages": [AIMessage(content=f"Processing custom request: {human_decision}")],
            }
    
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
