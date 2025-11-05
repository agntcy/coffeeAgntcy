# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ioa_observe.sdk.tracing import session_start
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

setup_logging()
logger = logging.getLogger("lungo.supervisor.main")

load_dotenv()

# Initialize the shared agntcy factory with tracing enabled
shared.set_factory(AgntcyFactory("lungo.exchange", enable_tracing=True))

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
  prompt: str

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
    session_start() # Start a new tracing session for observability
    
    # Execute the graph synchronously - blocks until completion
    result = await exchange_graph.serve(request.prompt)
    logger.info(f"Final result from LangGraph: {result}")
    return {"response": result}
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
        session_start()  # Start a new tracing session for observability

        async def stream_generator():
            """
            Generator that yields JSON chunks as they arrive from the graph.
            Uses newline-delimited JSON (NDJSON) format for streaming.
            """
            try:
                # Stream chunks from the graph as nodes complete execution
                async for chunk in exchange_graph.streaming_serve(request.prompt):
                    yield json.dumps({"response": chunk}) + "\n"
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
  Return suggested prompts for publish subscribe pattern.

  Args:
      pattern: Pattern type ("default" for all prompts, "streaming" for streaming-specific prompts)

  Returns:
  {"buyer": List[str], "purchaser": List[str]}

  Raises:
      HTTPException: 404 if file not found, 500 for JSON errors or unsupported format
  """
  if pattern == "streaming":
    prompts_path = Path(__file__).resolve().parent / "suggested_streaming_prompts.json"
  else:
    prompts_path = Path(__file__).resolve().parent / "suggested_prompts.json"
  try:
    raw = prompts_path.read_text(encoding="utf-8")
    data = json.loads(raw)

    if isinstance(data, dict):
      raw_buyer = data.get("buyer", [])
      raw_purchaser = data.get("purchaser", [])

      if not isinstance(raw_buyer, list):
        raw_buyer = []
      if not isinstance(raw_purchaser, list):
        raw_purchaser = []

      buyer_list = [p for p in raw_buyer if isinstance(p, str)]
      purchaser_list = [p for p in raw_purchaser if isinstance(p, str)]
      return {"buyer": buyer_list, "purchaser": purchaser_list}
    
    elif isinstance(data, list):
      prompt_list = [p for p in data if isinstance(p, str)]
      return {"buyer": prompt_list, "purchaser": []}

    logger.error("Unsupported JSON format in %s: %s", 
                 "suggested_streaming_prompts.json" if pattern == "streaming" else "suggested_prompts.json", 
                 type(data).__name__)
    raise HTTPException(status_code=500, detail="Unsupported JSON format")

  except FileNotFoundError as fnf:
    filename = "suggested_streaming_prompts.json" if pattern == "streaming" else "suggested_prompts.json"
    logger.exception(f"{filename} not found at {prompts_path}")
    raise HTTPException(status_code=404, detail=f"{filename} not found") from fnf
  except json.JSONDecodeError as jde:
    filename = "suggested_streaming_prompts.json" if pattern == "streaming" else "suggested_prompts.json"
    logger.exception(f"Invalid JSON in {filename}")
    raise HTTPException(status_code=500, detail=f"Invalid JSON in {filename}") from jde
  except Exception as e:
    if isinstance(e, HTTPException):
      raise
    logger.exception(f"Failed to load suggested prompts: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Failed to load prompts: {str(e)}") from e

# Run the FastAPI server using uvicorn
if __name__ == "__main__":
  uvicorn.run("agents.supervisors.auction.main:app", host="0.0.0.0", port=8000, reload=True)
