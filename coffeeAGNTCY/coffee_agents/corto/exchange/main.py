# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
import json

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from agntcy_app_sdk.factory import AgntcyFactory
from ioa_observe.sdk.tracing import session_start
from common.version import get_version_info

from config.logging_config import setup_logging
from exchange.agent import ExchangeAgent

setup_logging()
logger = logging.getLogger("corto.supervisor.main")
load_dotenv()

# Initialize the agntcy factory with tracing enabled
factory = AgntcyFactory("corto.exchange", enable_tracing=True)

app = FastAPI()
# Add CORS middleware
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],  # Replace "*" with specific origins if needed
  allow_credentials=True,
  allow_methods=["*"],  # Allow all HTTP methods
  allow_headers=["*"],  # Allow all headers
)

exchange_agent = ExchangeAgent(factory=factory)

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
    with session_start() as session_id:
      # Process the prompt using the exchange graph
      result = await exchange_agent.execute_agent_with_llm(request.prompt)
      logger.info(f"Final result from exchange agent: {result}")
      return {"response": result, "session_id": session_id["executionID"]}
  except ValueError as ve:
    logger.exception(f"ValueError occurred: {str(ve)}")
    raise HTTPException(status_code=400, detail=str(ve))
  except Exception as e:
    logger.exception(f"An error occurred: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/about")
async def version_info():
  """Return minimal build info sourced from about.properties."""
  props_path = Path(__file__).parent.parent / "about.properties"
  return get_version_info(props_path)

@app.get("/suggested-prompts")
async def get_prompts():
  """
  Returns a list of suggested prompts as a JSON array.

  Returns:
      list: A list of suggested prompt strings loaded from suggested_prompts.json.
  """
  prompts_path = Path(__file__).parent / "suggested_prompts.json"
  try:
    raw = prompts_path.read_text(encoding="utf-8")
    return json.loads(raw)
  except FileNotFoundError as fnf:
    logger.exception(f"suggested_prompts.json not found at {prompts_path}")
    raise HTTPException(status_code=404, detail="suggested_prompts.json not found") from fnf
  except json.JSONDecodeError as jde:
    logger.exception("Invalid JSON in suggested_prompts.json")
    raise HTTPException(status_code=500, detail="Invalid JSON in suggested_prompts.json") from jde
  except Exception as e:
    logger.exception(f"Failed to load suggested prompts: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Failed to load prompts: {str(e)}") from e

# Run the FastAPI server using uvicorn
if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)