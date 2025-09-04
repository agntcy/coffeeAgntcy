# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from config.logging_config import setup_logging
from graph.graph import ExchangeGraph
from dotenv import load_dotenv
from graph import shared
from agntcy_app_sdk.factory import AgntcyFactory
from ioa_observe.sdk.tracing import session_start
from config.config import DEFAULT_MESSAGE_TRANSPORT
from services.component_discovery import ComponentDiscoveryService

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
component_discovery = ComponentDiscoveryService()

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

@app.get("/topology/components")
async def get_topology_components(pattern: str = "publish_subscribe"):
    """
    Discovers and returns available topology components for the specified pattern.
    
    Args:
        pattern: The topology pattern name (e.g., 'publish_subscribe')
    
    Returns:
        dict: Complete topology structure with nodes, edges, and transport information
    """
    try:
        components = await component_discovery.discover_components(pattern)
        
        return {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.type,
                    "name": node.name,
                    "verification": node.verification,
                    "github_url": node.github_url,
                    "data": node.data
                }
                for node in components.nodes
            ],
            "edges": [
                {
                    "id": edge.id,
                    "source": edge.source,
                    "target": edge.target,
                    "sourceHandle": edge.source_handle,
                    "targetHandle": edge.target_handle,
                    "data": edge.data,
                    "type": edge.type
                }
                for edge in components.edges
            ],
            "transport": components.transport
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to discover components: {e}")
        raise HTTPException(status_code=500, detail=f"Component discovery failed: {str(e)}")

# Run the FastAPI server using uvicorn
if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)