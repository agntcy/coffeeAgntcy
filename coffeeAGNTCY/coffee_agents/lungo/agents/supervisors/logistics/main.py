# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from fastapi.responses import StreamingResponse
from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.semantic.a2a.protocol import A2AProtocol
from ioa_observe.sdk.tracing import session_start

from agents.supervisors.logistics.graph.graph import LogisticGraph
from agents.supervisors.logistics.graph import shared
from agents.logistics.shipper.card import AGENT_CARD  # assuming similar structure
from config.config import DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT
from config.logging_config import setup_logging
from pathlib import Path

setup_logging()
logger = logging.getLogger("lungo.logistics.supervisor.main")

load_dotenv()

# Initialize the shared agntcy factory with tracing enabled
shared.set_factory(AgntcyFactory("lungo.logistics_supervisor", enable_tracing=True))

app = FastAPI()
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

logistic_graph = LogisticGraph()

class PromptRequest(BaseModel):
  prompt: str

@app.post("/agent/prompt")
async def handle_prompt(request: PromptRequest):
  try:
    with session_start() as session_id:
      timeout_val = int(os.getenv("LOGISTIC_TIMEOUT", "200"))
      result = await asyncio.wait_for(
        logistic_graph.serve(request.prompt),
        timeout=timeout_val
      )
      logger.info(f"Final result from LangGraph: {result}")
      return {"response": result, "session_id": session_id["executionID"]}
  except asyncio.TimeoutError:
    logger.error("Request timed out after %s seconds", timeout_val)
    raise HTTPException(status_code=504, detail=f"Request timed out after {timeout_val} seconds")
  except ValueError as ve:
    raise HTTPException(status_code=400, detail=str(ve))
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")

@app.get("/health")
async def health_check():
  return {"status": "ok"}

@app.get("/v1/health")
async def connectivity_health():
  """
  Deep liveness: validates transport + client creation.
  """
  try:
    factory = shared.get_factory() if hasattr(shared, "get_factory") else shared.factory  # fallback
    transport = factory.create_transport(
      DEFAULT_MESSAGE_TRANSPORT,
      endpoint=TRANSPORT_SERVER_ENDPOINT,
      name="default/default/liveness_probe",
    )
    _ = await asyncio.wait_for(
      factory.create_client(
        "A2A",
        agent_topic=A2AProtocol.create_agent_topic(AGENT_CARD),
        transport=transport,
      ),
      timeout=30,
    )
    return {"status": "alive"}
  except asyncio.TimeoutError:
    raise HTTPException(status_code=500, detail="Timeout creating A2A client")
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/transport/config")
async def get_config():
  return {
    "transport": DEFAULT_MESSAGE_TRANSPORT.upper()
  }


@app.post("/agent/prompt/stream")
async def handle_stream_prompt(request: PromptRequest):
    """
    Streams real-time order processing events as they occur in the logistics workflow.

    Flow:
    1. Extracts order parameters (farm, quantity, price) from user prompt using LLM
    2. Initiates order with logistics agents (farm, shipper, accountant)
    3. Streams each status update as agents process the order:
       - RECEIVED_ORDER: Supervisor sends order to farm
       - HANDOVER_TO_SHIPPER: Farm hands off to shipper
       - CUSTOMS_CLEARANCE: Shipper clears customs
       - PAYMENT_COMPLETE: Accountant confirms payment
       - DELIVERED: Shipper completes delivery
    4. Sends final formatted summary message

    Args:
        request (PromptRequest): User's order request (e.g., "Order 5000 lbs at $3.52 from Tatooine")

    Returns:
        StreamingResponse: NDJSON stream where each line is:
        {"response": {"order_id": "...", "sender": "...", "state": "...", ...}} for events
        {"response": "Order X from Y for Z units at $W has been successfully delivered."} for summary

    Raises:
        HTTPException: 400 for invalid input, 500 for server-side errors.
    """
    try:
        with session_start() as session_id:  # Start a new tracing session for observability

          async def stream_generator():
              try:
                  async for chunk in logistic_graph.streaming_serve(request.prompt):
                      yield json.dumps({"response": chunk, "session_id": session_id["executionID"]}) + "\n"
              except Exception as e:
                  logger.error(f"Error in stream: {e}")
                  yield json.dumps({"response": f"Error: {str(e)}"}) + "\n"

          return StreamingResponse(
              stream_generator(),
              media_type="application/x-ndjson",
              headers={
                  "Cache-Control": "no-cache",
                  "Connection": "keep-alive",
              }
          )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")

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

    return {"logistics": data.get("logistics_prompts", [])}

  except Exception as e:
    logger.error(f"Unexpected error while reading prompts: {str(e)}")
    raise HTTPException(status_code=500, detail="An unexpected error occurred while reading prompts.")

if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=9090, reload=True)
