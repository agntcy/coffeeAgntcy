# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from agntcy_app_sdk.factory import AgntcyFactory
from ioa_observe.sdk.tracing import session_start

from agents.supervisors.logistic.graph.graph import LogisticGraph
from agents.supervisors.logistic.graph import shared
from config.config import DEFAULT_MESSAGE_TRANSPORT
from config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("lungo.logistic.supervisor.main")

load_dotenv()

# Initialize the shared agntcy factory with tracing enabled
shared.set_factory(AgntcyFactory("lungo.logistic", enable_tracing=True))

app = FastAPI()
# Add CORS middleware
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],  # Replace "*" with specific origins if needed
  allow_credentials=True,
  allow_methods=["*"],  # Allow all HTTP methods
  allow_headers=["*"],  # Allow all headers
)

logistic_graph = LogisticGraph()

class PromptRequest(BaseModel):
  prompt: str

@app.post("/agent/prompt")
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
    session_start() # Start a new tracing session
    # Process the prompt using the exchange graph
    result = await asyncio.wait_for(logistic_graph.serve(request.prompt), timeout=os.getenv("LOGISTIC_TIMEOUT", 200))
    logger.info(f"Final result from LangGraph: {result}")
    return {"response": result}
  except asyncio.TimeoutError:
    logger.error("Request timed out after %s seconds", os.getenv("LOGISTIC_TIMEOUT", 200))
    raise HTTPException(status_code=504, detail=f"Request timed out after {os.getenv("LOGISTIC_TIMEOUT", 200)} seconds")
  except ValueError as ve:
    raise HTTPException(status_code=400, detail=str(ve))
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/transport/config")
async def get_config():
    """
    Returns the current transport configuration.
    
    Returns:
        dict: Configuration containing transport settings.
    """
    return {
        "transport": DEFAULT_MESSAGE_TRANSPORT.upper()
    }

# Run the FastAPI server using uvicorn
if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=9090, reload=True)


