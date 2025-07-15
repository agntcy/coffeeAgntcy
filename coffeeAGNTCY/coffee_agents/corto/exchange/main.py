# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
    This endpoint processes the prompt using the exchange graph and returns the result.
    Args:
      request (PromptRequest): The input prompt from the user.
    Returns:
      dict: A dictionary containing the response from the ExchangeGraph.
    """
    try:
        # For backward compatibility, use simple prompt-only workflow
        hax_ready_messages = await exchange_graph.serve(request.prompt)
        # Find the first assistant text message and return its content
        for message in hax_ready_messages:
            if message["type"] == "TextMessage" and message["role"] == "assistant":
                return {"response": message["content"].strip()}
        raise RuntimeError("No valid assistant message found")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
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
