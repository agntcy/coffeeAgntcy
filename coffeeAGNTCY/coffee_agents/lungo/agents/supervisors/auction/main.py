# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import json
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ioa_observe.sdk.tracing import session_start
from pydantic import BaseModel
import uvicorn

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
    result = await exchange_graph.serve(request.prompt)
    logger.info(f"Final result from LangGraph: {result}")
    return {"response": result}
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
async def get_prompts():
  """
  Return suggested prompts for publish subscribe pattern.

  Returns:
  {"buyer": List[str], "purchaser": List[str]}

  Raises:
      HTTPException: 404 if file not found, 500 for JSON errors or unsupported format
  """
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

    logger.error("Unsupported suggested_prompts.json format: %s", type(data).__name__)
    raise HTTPException(status_code=500, detail="Unsupported suggested_prompts.json format")

  except FileNotFoundError as fnf:
    logger.exception(f"suggested_prompts.json not found at {prompts_path}")
    raise HTTPException(status_code=404, detail="suggested_prompts.json not found") from fnf
  except json.JSONDecodeError as jde:
    logger.exception("Invalid JSON in suggested_prompts.json")
    raise HTTPException(status_code=500, detail="Invalid JSON in suggested_prompts.json") from jde
  except Exception as e:
    if isinstance(e, HTTPException):
      raise
    logger.exception(f"Failed to load suggested prompts: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Failed to load prompts: {str(e)}") from e

# Run the FastAPI server using uvicorn
if __name__ == "__main__":
  uvicorn.run("agents.supervisors.auction.main:app", host="0.0.0.0", port=8000, reload=True)