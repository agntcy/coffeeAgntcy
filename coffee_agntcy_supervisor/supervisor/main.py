# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Start the FastAPI application using Uvicorn
import asyncio
import os
import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from uvicorn import Config, Server
from supervisor.api.routes import stateless_runs


def create_app() -> FastAPI:
  """
  Creates and configures the FastAPI application instance.

  This function sets up:
  - The API metadata (title, version, OpenAPI URL).
  - CORS middleware to allow cross-origin requests.
  - Route handlers for API endpoints.
  - A custom unique ID generator for API routes.

  Returns:
      FastAPI: The configured FastAPI application instance.
  """
  app = FastAPI(
    title="Acorda Agent Supervisor",
    openapi_url=f"/api/v1/openapi.json",
    version="0.1.0",
    description="Acorda Agent Supervisor API",
  )

  app.include_router(stateless_runs.router, prefix="/api/v1")

  # Set all CORS enabled origins
  app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
  )

  return app


def main() -> None:
  """
  Entry point for running the FastAPI application.

  This function performs the following:
  - Configures logging globally.
  - Loads environment variables from a `.env` file.
  - Retrieves the port from environment variables (default: 8125).
  - Starts the Uvicorn server.

  Returns:
      None
  """
  logger = logging.getLogger("app")  # Default logger for main script
  logger.info("Starting FastAPI application...")

  # Determine port number from environment variables or use the default
  port = int(os.getenv("ACORDA_AGENT_PORT", "8125"))

  config = Config(
    app=create_app(),
    host="0.0.0.0",
    port=port,
    log_level="info",
  )
  server = Server(config)

  if asyncio.get_event_loop().is_running():
    # If running inside an existing event loop
    asyncio.ensure_future(server.serve())
  else:
    asyncio.run(server.serve())


if __name__ == "__main__":
  main()
