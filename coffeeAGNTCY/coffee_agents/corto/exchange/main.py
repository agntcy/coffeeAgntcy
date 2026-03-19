# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from pathlib import Path

import uvicorn
from agntcy_app_sdk.factory import AgntcyFactory
from common.version import get_version_info
from config.logging_config import setup_logging
from dotenv import load_dotenv
from exchange.agent import ExchangeAgent
from exchange.errors import RemoteAgentNoResponseError, TransportTimeoutError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ioa_observe.sdk.tracing import session_start
from pydantic import BaseModel

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
      HTTPException: 400 for invalid input, 504 for gateway timeout (remote agent did not respond in time),
      502 for bad gateway (remote agent returned no response / invalid payload), 500 for other server-side errors.
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
  except TransportTimeoutError as e:
    logger.exception("Transport timeout: %s", e)
    detail = "Remote agent did not respond in time (SLIM receive timeout)."
    if e.__cause__ is not None:
      detail = f"{detail} Cause: {e.__cause__}"
    raise HTTPException(status_code=504, detail=detail)
  except RemoteAgentNoResponseError as e:
    logger.exception("Remote agent returned no response: %s", e)
    detail = "Remote agent returned no response (missing or invalid payload)."
    if e.__cause__ is not None:
      detail = f"{detail} Cause: {e.__cause__}"
    raise HTTPException(status_code=502, detail=detail)
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


@app.get("/agents/{slug}/oasf")
async def get_agent_oasf(slug: str):
    """
    Returns the OASF JSON for the specified agent slug from the static files.
    """
    if slug not in ["exchange-supervisor-agent", "flavor-profile-farm-agent"]:
        raise HTTPException(status_code=404, detail="OASF record not found")

    oasf_path = (
        Path(__file__).resolve().parent.parent / "oasf" / "agents" / f"{slug}.json"
    )
    if not oasf_path.exists():
        raise HTTPException(status_code=404, detail="OASF record not found")

    try:
        with oasf_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Failed to read OASF file for slug '{slug}': {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving the agent information. Please try again later.",
        ) from e


# Run the FastAPI server using uvicorn
if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
