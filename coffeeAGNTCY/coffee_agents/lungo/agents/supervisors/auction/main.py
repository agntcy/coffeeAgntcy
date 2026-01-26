# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from fastapi.responses import StreamingResponse
import json
from agntcy_app_sdk.factory import AgntcyFactory
from ioa_observe.sdk.tracing import session_start

from agents.supervisors.auction.graph.graph import ExchangeGraph
from agents.supervisors.auction.graph import shared
from config.config import DEFAULT_MESSAGE_TRANSPORT
from config.logging_config import setup_logging
from pathlib import Path
from common.version import get_version_info
from agents.supervisors.auction.api import create_apps_router
from fastapi import HTTPException

setup_logging()
logger = logging.getLogger("lungo.supervisor.main")

load_dotenv()

# Initialize the shared agntcy factory with tracing enabled
shared.set_factory(AgntcyFactory("lungo.auction_supervisor", enable_tracing=True))

app = FastAPI()
# Add CORS middleware
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],  # Replace "*" with specific origins if needed
  allow_credentials=True,
  allow_methods=["*"],  # Allow all HTTP methods
  allow_headers=["*"],  # Allow all headers
)

app.include_router(create_apps_router())

exchange_graph = ExchangeGraph()

class PromptRequest(BaseModel):
  prompt: str

@app.get("/.well-known/agent.json")
async def get_capabilities():
  """
  Returns the capabilities of the auction supervisor.

  Returns:
      dict: A dictionary containing the capabilities and metadata of the auction supervisor.
  """
  return {
    "capabilities": {"streaming": True},
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
    "description": "An AI agent that supervises auctions and manages coffee farm operations.",
    "name": "Auction Supervisor",
    "preferredTransport": "JSONRPC",
    "protocolVersion": "0.3.0",
    "skills": [
      {
        "description": "Supervises auctions and manages coffee farm operations.",
        "examples": [
          "What is the yield of the Vietnam coffee farm?",
          "How much coffee does the Vietnam farm produce?",
          "What is the yield of the Vietnam coffee farm in pounds?",
          "How many pounds of coffee does the Vietnam farm produce?",
        ],
        "id": "get_yield",
        "name": "Get Coffee Yield",
        "tags": ["coffee", "farm", "auction"],
      }
    ],
    "supportsAuthenticatedExtendedCard": False,
    "url": "",
    "version": "1.0.0",
  }

@app.post("/agent/prompt")
async def handle_prompt(request: PromptRequest):
  """
  Processes a user prompt by routing it through the ExchangeGraph.
  
  This endpoint uses the non-streaming serve() method, which waits for the entire
  graph execution to complete before returning the final response.

  Args:
      request (PromptRequest): Contains the input prompt as a string.

  Returns:
      dict: A dictionary containing the agent's response.

  Raises:
      HTTPException: 400 for invalid input, 500 for server-side errors.
  """
  try:
    with session_start() as session_id:
    
    # Execute the graph synchronously - blocks until completion
      result = await exchange_graph.serve(request.prompt)
      logger.info(f"Final result from LangGraph: {result}")
      return {"response": result, "session_id": session_id["executionID"]}
  except ValueError as ve:
    raise HTTPException(status_code=400, detail=str(ve))
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")


@app.post("/agent/prompt/stream")
async def handle_stream_prompt(request: PromptRequest):
    """
    Processes a user prompt and streams the response from the ExchangeGraph.
    
    This endpoint uses the streaming_serve() method to provide real-time updates
    as the graph executes, yielding chunks progressively from each node.

    Args:
        request (PromptRequest): Contains the input prompt as a string.

    Returns:
        StreamingResponse: JSON stream with node outputs as they complete.
        Each chunk is formatted as: {"response": "..."}

    Raises:
        HTTPException: 400 for invalid input, 500 for server-side errors.
    """
    try:
        with session_start() as session_id: # Start a new tracing session for observability

          async def stream_generator():
              """
              Generator that yields JSON chunks as they arrive from the graph.
              Uses newline-delimited JSON (NDJSON) format for streaming.
              """
              try:
                  # Stream chunks from the graph as nodes complete execution
                  async for chunk in exchange_graph.streaming_serve(request.prompt):
                      yield json.dumps({"response": chunk, "session_id": session_id["executionID"]}) + "\n"
              except Exception as e:
                  logger.error(f"Error in stream: {e}")
                  yield json.dumps({"response": f"Error: {str(e)}"}) + "\n"

          return StreamingResponse(
              stream_generator(),
              media_type="application/x-ndjson",  # Newline-delimited JSON for streaming
              headers={
                  "Cache-Control": "no-cache",  # Prevent caching of streaming responses
                  "Connection": "keep-alive",   # Keep connection open for streaming
              }
          )
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

@app.get("/about")
async def version_info():
  """Return build info sourced from about.properties."""
  props_path = Path(__file__).resolve().parents[3] / "about.properties"
  return get_version_info(props_path)

@app.get("/suggested-prompts")
async def get_prompts(pattern: str = "default"):
  """
  Fetch suggested prompts based on the specified pattern.

  Parameters:
      pattern (str): The type of prompts to fetch.
                     Use "default" for all prompts or "streaming" for streaming-specific prompts.

  Returns:
      dict: A dictionary containing lists of prompts for "buyer" and "purchaser".

  Raises:
      HTTPException:
          - 500 if the JSON file is invalid or an unexpected error occurs.
  """
  try:
    prompts_path = Path(__file__).resolve().parent / "suggested_prompts.json"
    raw = prompts_path.read_text(encoding="utf-8")
    data = json.loads(raw)

    if pattern == "streaming":
      streaming_prompts = data.get("streaming_prompts", [])
      return {"streaming": streaming_prompts}

    buyer_prompts = data.get("buyer", [])
    purchaser_prompts = data.get("purchaser", [])
    return {"buyer": buyer_prompts, "purchaser": purchaser_prompts}

  except Exception as e:
    logger.error(f"Unexpected error while reading prompts: {str(e)}")
    raise HTTPException(status_code=500, detail="An unexpected error occurred while reading prompts.")

# Run the FastAPI server using uvicorn
if __name__ == "__main__":
  uvicorn.run("agents.supervisors.auction.main:app", host="0.0.0.0", port=8000, reload=True)
