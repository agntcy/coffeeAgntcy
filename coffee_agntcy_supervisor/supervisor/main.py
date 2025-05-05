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

import argparse
import asyncio
import os

from uvicorn import Config, Server
from supervisor.graph.graph import SupervisorGraph
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from supervisor.api.routes import stateless_runs


def create_app() -> FastAPI:
  app = FastAPI(
    title="Acorda Agent Supervisor",
    openapi_url="/api/v1/openapi.json",
    version="0.1.0",
    description="Acorda Agent Supervisor API",
  )
  app.include_router(stateless_runs.router, prefix="/api/v1")
  app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
  )
  return app


def run_server():
  port = int(os.getenv("ACORDA_AGENT_PORT", "8125"))
  config = Config(
    app=create_app(),
    host="0.0.0.0",
    port=port,
    log_level="info",
  )
  server = Server(config)
  if asyncio.get_event_loop().is_running():
    asyncio.ensure_future(server.serve())
  else:
    asyncio.run(server.serve())


def run_graph():
  supervisor_graph = SupervisorGraph()
  user_prompt = "Sample user input for SupervisorGraph"
  result, _ = supervisor_graph.serve(user_prompt)
  print("SupervisorGraph result:", result)


def main():
  parser = argparse.ArgumentParser(description="Run Acorda Agent Supervisor")
  parser.add_argument(
    "--server",
    action="store_true",
    help="Run the FastAPI server. If not provided, the SupervisorGraph will be invoked directly.",
  )
  args = parser.parse_args()

  if args.server:
    run_server()
  else:
    run_graph()

if __name__ == "__main__":
  main()