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
from agntcy_app_sdk.protocols.a2a.protocol import A2AProtocol
from ioa_observe.sdk.tracing import session_start

from agents.supervisors.logistic.graph.graph import LogisticGraph
from agents.supervisors.logistic.graph import shared
from agents.logistics.shipper.card import AGENT_CARD  # assuming similar structure
from config.config import DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT
from config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("lungo.logistic.supervisor.main")

load_dotenv()

# Initialize the shared agntcy factory with tracing enabled
shared.set_factory(AgntcyFactory("lungo.logistic", enable_tracing=True))

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
    session_start()
    timeout_val = int(os.getenv("LOGISTIC_TIMEOUT", "200"))
    result = await asyncio.wait_for(
      logistic_graph.serve(request.prompt),
      timeout=timeout_val
    )
    logger.info(f"Final result from LangGraph: {result}")
    return {"response": result}
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

if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=9090, reload=True)
