# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from graph.graph import ExchangeGraph
from pydantic import BaseModel

from config.logging_config import setup_logging
from exchange.models import Action

setup_logging()
logger = logging.getLogger("corto.supervisor.main")

app = FastAPI()
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

exchange_graph = ExchangeGraph()


class PromptRequest(BaseModel):
    """Simple prompt request with only text input"""

    prompt: str


class ChatRequest(BaseModel):
    """Full chat request with actions and messages"""

    prompt: str
    actions: list[Action] = []


@app.post(
    "/agent/prompt",
    description="Legacy endpoint for simple prompt-response interaction",
    response_description="A simple text response to the input prompt",
    responses={
        200: {
            "description": "Successfully generated response",
            "content": {
                "application/json": {
                    "example": {
                        "response": "Colombian coffee in winter typically exhibits notes of dark chocolate and caramel."
                    }
                }
            },
        }
    },
)
async def handle_prompt(request: PromptRequest):
    """
    Processes a user prompt by routing it through the ExchangeGraph.

    Args:
        request (PromptRequest): Contains the input prompt as a string.

    Returns:
        dict: A dictionary containing the agent's response.

    Raises:
        HTTPException: 400 for invalid input, 500 for server-side errors.
    """
    try:
        # Process the prompt using the exchange graph
        result = await exchange_graph.serve(request.prompt)
        logger.info(f"Final result from LangGraph: {result}")
        return {"response": result}
    except ValueError as ve:
        logger.exception(f"ValueError occurred: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")
    
@app.post(
    "/agent/chat",
    description="Enhanced endpoint supporting actions and full message history",
    response_description="Complete chat history including tool calls and their results",
    responses={
        200: {
            "description": "Successfully processed chat request",
            "content": {
                "application/json": {
                    "example": [
                        {"role": "user", "content": "What are the flavor notes?"},
                        {
                            "role": "assistant",
                            "content": "Analyzing flavor profile...",
                            "tool_calls": [
                                {
                                    "name": "get_flavor_profile",
                                    "args": {
                                        "location": "Colombia",
                                        "season": "winter",
                                    },
                                }
                            ],
                        },
                    ]
                }
            },
        }
    },
)
async def handle_chat(request: ChatRequest):
    """
    Enhanced endpoint that supports actions and returns full message history.
    """
    try:
        # Get messages in HAX-ready format
        hax_ready_messages = await exchange_graph.serve(request.prompt, request.actions)
        logger.info(f"Final result from LangGraph: {hax_ready_messages}")
        return {"messages": hax_ready_messages}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Run the FastAPI server using uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
