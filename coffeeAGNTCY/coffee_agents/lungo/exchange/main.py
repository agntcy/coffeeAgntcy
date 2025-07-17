# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# from config.logging_config import setup_logging
from graph.graph import ExchangeGraph
from exchange.utils.identity_utils import initialize_clients_and_issue_badges
from exchange.utils.config import vietnam_farm_url, columbia_farm_url, brazil_farm_url
from farms.brazil.card import AGENT_CARD as brazil_agent_card
from farms.colombia.card import AGENT_CARD as colombia_agent_card
from farms.vietnam.card import AGENT_CARD as vietnam_agent_card

# setup_logging()
logger = logging.getLogger("corto.supervisor.main")

# Global variables
exchange_graph = ExchangeGraph()

@asynccontextmanager
async def lifespan(app: FastAPI):
  global badge_verification
  try:
    # Retrieve URLs from environment variables
    hydra_admin_url = os.getenv("HYDRA_CLIENT_API_URL", "http://127.0.0.1:4445/clients")
    idp_url = os.getenv("IDP_ISSUER_URL")
    register_issuer = os.getenv("REGISTER_ISSUER", "false").lower() == "true" # Set this to true if idp url is new
    identity_node_api_url = os.getenv("IDENTITY_NODE_API_URL", "https://api.identity-node.dev.outshift.ai")

    logger.info(f"All environment variables: HYDRA_CLIENT_API_URL={hydra_admin_url}, IDP_ISSUER_URL={idp_url}, IDENTITY_NODE_API_URL={identity_node_api_url}, REGISTER_ISSUER={register_issuer}")

    if idp_url:
      farm_agent_urls = {
        vietnam_agent_card.name: vietnam_farm_url,
        colombia_agent_card.name: columbia_farm_url,
        brazil_agent_card.name: brazil_farm_url,
      }
      # farm_agent_urls = [vietnam_farm_url, columbia_farm_url, brazil_farm_url]
      # Initialize clients and issue badges
      farm_client_id_map = initialize_clients_and_issue_badges(hydra_admin_url, idp_url, farm_agent_urls, register_issuer, identity_node_api_url)

      for farm_agent_name, client_id in farm_client_id_map.items():
        badge_url = f"{identity_node_api_url}/v1alpha1/vc/IDP-{client_id}/.well-known/vcs.json"
        logger.info(f"Farm name: {farm_agent_name}, Badge URL: {badge_url}")

      if farm_client_id_map == {}:
        logger.warning("Badge issuance failed. Badge verification will be disabled.")
    else:
      logger.warning("Required environment variables are not set. Skipping client initialization.")
    yield
  except Exception as e:
    logger.error(f"Failed to initialize clients: {e}")

  finally:
    logger.info("Application shutdown. Cleaning up resources if needed.")

# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],  # Replace "*" with specific origins if needed
  allow_credentials=True,
  allow_methods=["*"],  # Allow all HTTP methods
  allow_headers=["*"],  # Allow all headers
)

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

# Run the FastAPI server using uvicorn
if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
