# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from agntcy_app_sdk.factory import AgntcyFactory
from ioa_observe.sdk.tracing import session_start

from config.logging_config import setup_logging
from exchange.graph import shared
from exchange.graph.graph import ExchangeGraph

setup_logging()
logger = logging.getLogger("corto.supervisor.main")
load_dotenv()

# Initialize the shared agntcy factory with tracing enabled
shared.set_factory(AgntcyFactory("corto.exchange", enable_tracing=True))

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
    logger.exception(f"ValueError occurred: {str(ve)}")
    raise HTTPException(status_code=400, detail=str(ve))
  except Exception as e:
    logger.exception(f"An error occurred: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Run the FastAPI server using uvicorn
if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)