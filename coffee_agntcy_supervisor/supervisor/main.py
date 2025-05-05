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
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from uvicorn import Config, Server

from supervisor.api.routes import stateless_runs
from supervisor.common.config import get_settings_from_env
from supervisor.common.logging_config import configure_logging, logging


def load_environment_variables(env_file: str | None = None) -> None:
  """
  Load environment variables from a .env file safely.

  This function loads environment variables from a `.env` file, ensuring
  that critical configurations are set before the application starts.

  Args:
    env_file (str | None): Path to a specific `.env` file. If None,
                            it searches for a `.env` file automatically.

  Behavior:
  - If `env_file` is provided, it loads the specified file.
  - If `env_file` is not provided, it attempts to locate a `.env` file in the project directory.
  - Logs a warning if no `.env` file is found.

  Returns:
    None
  """
  env_path = env_file or find_dotenv()

  if env_path:
    load_dotenv(env_path, override=True)
    logging.info(f".env file loaded from {env_path}")
  else:
    logging.warning("No .env file found. Ensure environment variables are set.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
  """
  Defines startup and shutdown logic for the FastAPI application.

  This function follows the `lifespan` approach, allowing resource initialization
  before the server starts and cleanup after it shuts down.

  Args:
      app (FastAPI): The FastAPI application instance.

  Yields:
      None: The application runs while `yield` is active.

  Behavior:
  - On startup: Logs a startup message.
  - On shutdown: Logs a shutdown message.
  - Can be extended to initialize resources (e.g., database connections).
  """
  logging.info("Starting Acorda Supervisor Agent...")

  # Example: Attach database connection to app state (if needed)
  # app.state.db = await init_db_connection()

  yield  # Application runs while 'yield' is in effect.

  logging.info("Application shutdown")

  # Example: Close database connection (if needed)
  # await app.state.db.close()


def custom_generate_unique_id(route: APIRoute) -> str:
  """
  Generates a unique identifier for API routes.

  Args:
      route (APIRoute): The FastAPI route object.

  Returns:
      str: A unique string identifier for the route.

  Behavior:
  - If the route has tags, the ID is formatted as `{tag}-{route_name}`.
  - If no tags exist, the route name is used as the ID.
  """
  if route.tags:
    return f"{route.tags[0]}-{route.name}"
  return route.name


def add_health_check_handler(app: FastAPI) -> None:
  """
  Adds a health check endpoint to the FastAPI application.
  """

  @app.get("/healthz")
  def health_check():
    return {
      "service_name": "acorda-agntcy-agent",
      "service_state": "Up",
      "last_updated": datetime.now().isoformat(),
    }


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
  settings = get_settings_from_env()
  app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    version="0.1.0",
    description=settings.PROJECT_NAME,
    lifespan=lifespan,  # Use the new lifespan approach for startup/shutdown
  )

  add_health_check_handler(app)
  app.include_router(stateless_runs.router, prefix=settings.API_V1_STR)

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
  configure_logging()  # Apply global logging settings

  logger = logging.getLogger("app")  # Default logger for main script
  logger.info("Starting FastAPI application...")

  # Load environment variables before starting the application
  load_environment_variables()

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
