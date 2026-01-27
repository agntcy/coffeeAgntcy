# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Human-in-the-Loop API Endpoints
================================

This module provides FastAPI endpoints for the HITL-enabled Exchange Graph,
supporting the interrupt/resume pattern for human intervention in order processing.

Purpose:
    Expose REST API endpoints that allow clients to:
    - Start HITL-enabled requests that may pause for human input
    - Resume paused requests with human decisions
    - Query information about HITL models and configuration

Endpoints:
    POST /agent/prompt/hitl
        Start a request with HITL enabled. May return with status
        'awaiting_human_input' if human intervention is needed.
        
    POST /agent/prompt/hitl/resume  
        Resume an interrupted request with the human's decision.
        Returns the final processed result.
        
    GET /agent/prompt/hitl/info
        Get information about HITL models and configuration.

Example Usage (curl):
    # Start a HITL request
    curl -X POST http://localhost:8000/agent/prompt/hitl \
        -H "Content-Type: application/json" \
        -d '{"prompt": "500 lbs, budget $2000"}'
    
    # Resume with human decision
    curl -X POST http://localhost:8000/agent/prompt/hitl/resume \
        -H "Content-Type: application/json" \
        -d '{"thread_id": "abc-123", "decision": "Balanced Diversification"}'

Reference: https://docs.langchain.com/oss/python/langgraph/interrupts
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ioa_observe.sdk.tracing import session_start

from agents.supervisors.auction.graph.graph_hitl import ExchangeGraphHITL

logger = logging.getLogger("lungo.supervisor.api_hitl")

# Initialize the HITL-enabled graph
hitl_graph = ExchangeGraphHITL(enable_hitl=True)


class HITLPromptRequest(BaseModel):
    """Request model for HITL-enabled prompts"""
    prompt: str = Field(..., description="The user's input prompt")
    thread_id: Optional[str] = Field(None, description="Optional thread ID for tracking")


class HITLResumeRequest(BaseModel):
    """Request model for resuming an interrupted HITL request"""
    thread_id: str = Field(..., description="The thread ID from the interrupted request")
    decision: str = Field(..., description="The human's decision (scenario name or custom instruction)")


class HITLResponse(BaseModel):
    """Response model for HITL requests"""
    status: str = Field(..., description="Status: 'completed', 'awaiting_human_input', or 'error'")
    response: Optional[str] = Field(None, description="The agent's response (if completed)")
    interrupt: Optional[dict] = Field(None, description="Interrupt payload (if awaiting human input)")
    thread_id: str = Field(..., description="Thread ID for this request")


def create_hitl_router() -> APIRouter:
    """Create the HITL API router"""
    router = APIRouter(prefix="/agent/prompt/hitl", tags=["hitl"])
    
    @router.post("", response_model=HITLResponse)
    async def handle_hitl_prompt(request: HITLPromptRequest):
        """
        Process a user prompt with Human-in-the-Loop enabled.
        
        This endpoint uses the HITL-enabled Exchange Graph which may pause
        execution for human intervention when complex decisions are detected.
        
        Flow:
        1. User sends a prompt (e.g., "I need to place our Q2 order. 500 lbs total, budget capped at $2,000")
        2. WHEN-TO-TRIGGER model evaluates if human intervention is needed
        3. If triggered:
           - WHAT-TO-RESPOND model generates options
           - Returns with status='awaiting_human_input' and interrupt payload
        4. If not triggered:
           - Proceeds with standard order processing
           - Returns with status='completed' and response
        
        Args:
            request: HITLPromptRequest with prompt and optional thread_id
        
        Returns:
            HITLResponse with status, response/interrupt, and thread_id
        
        Example Response (interrupted):
        ```json
        {
            "status": "awaiting_human_input",
            "interrupt": {
                "type": "human_intervention_required",
                "summary": "Order Analysis for: 500 lbs, Budget: $2,000.00...",
                "scenarios": [...],
                "recommendation": "Recommend 'Balanced Diversification'...",
                "instructions": "Please select one of the scenarios..."
            },
            "thread_id": "abc-123"
        }
        ```
        """
        try:
            session_start()  # Start tracing session
            
            logger.info(f"[HITL] Received prompt: {request.prompt}")
            
            result = await hitl_graph.serve(
                prompt=request.prompt,
                thread_id=request.thread_id,
            )
            
            # Check if we hit an interrupt
            if "interrupt" in result:
                return HITLResponse(
                    status="awaiting_human_input",
                    interrupt=result["interrupt"],
                    thread_id=result["thread_id"],
                )
            
            return HITLResponse(
                status="completed",
                response=result.get("response", ""),
                thread_id=result.get("thread_id", ""),
            )
            
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(f"[HITL] Error: {e}")
            raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")
    
    @router.post("/resume", response_model=HITLResponse)
    async def handle_hitl_resume(request: HITLResumeRequest):
        """
        Resume an interrupted HITL request with the human's decision.
        
        After receiving an interrupt response, the human reviews the options
        and makes a decision. This endpoint resumes graph execution with
        that decision.
        
        Flow:
        1. Human reviews the interrupt payload (scenarios, recommendations)
        2. Human selects a scenario or provides custom instructions
        3. Client calls this endpoint with thread_id and decision
        4. Graph resumes from the interrupt point
        5. Order is processed based on the human's decision
        6. Returns with status='completed' and final response
        
        Args:
            request: HITLResumeRequest with thread_id and decision
        
        Returns:
            HITLResponse with status and final response
        
        Example Request:
        ```json
        {
            "thread_id": "abc-123",
            "decision": "Balanced Diversification"
        }
        ```
        
        Example Response:
        ```json
        {
            "status": "completed",
            "response": "Executing order based on 'Balanced Diversification' scenario...",
            "thread_id": "abc-123"
        }
        ```
        """
        try:
            session_start()  # Start tracing session
            
            logger.info(f"[HITL] Resuming thread {request.thread_id} with decision: {request.decision}")
            
            result = await hitl_graph.resume(
                thread_id=request.thread_id,
                human_response=request.decision,
            )
            
            # Check if we hit another interrupt (unlikely but possible)
            if "interrupt" in result:
                return HITLResponse(
                    status="awaiting_human_input",
                    interrupt=result["interrupt"],
                    thread_id=result["thread_id"],
                )
            
            return HITLResponse(
                status="completed",
                response=result.get("response", ""),
                thread_id=result.get("thread_id", ""),
            )
            
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(f"[HITL] Resume error: {e}")
            raise HTTPException(status_code=500, detail=f"Resume failed: {str(e)}")
    
    @router.get("/info")
    async def get_hitl_info():
        """
        Get information about the HITL system.
        
        Returns details about the WHEN-TO-TRIGGER and WHAT-TO-RESPOND models,
        and example usage.
        """
        return {
            "name": "Human-in-the-Loop Coffee Exchange",
            "version": "1.0.0",
            "models": {
                "when_to_trigger": {
                    "name": "when-to-trigger-v1",
                    "description": "Analyzes context to decide if human intervention is needed",
                    "trigger_conditions": [
                        "Budget constraints detected",
                        "Missing origin/farm specification",
                        "Market volatility detected",
                        "Order would exceed budget",
                        "Complex multi-farm allocation needed",
                    ],
                    "threshold": 0.65,
                },
                "what_to_respond": {
                    "name": "what-to-respond-v1",
                    "description": "Generates options and scenarios for human review",
                    "outputs": [
                        "Multiple allocation scenarios",
                        "Cost-quality optimization",
                        "Supply chain risk analysis",
                        "Recommendations with rationale",
                    ],
                },
            },
            "example_prompt": "I need to place our Q2 order. 500 lbs total, budget capped at $2,000. What are our options?",
            "flow": [
                "1. Send prompt to POST /agent/prompt/hitl",
                "2. If interrupted, review scenarios in response",
                "3. Send decision to POST /agent/prompt/hitl/resume",
                "4. Receive final order confirmation",
            ],
        }
    
    return router
