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

import logging
from http import HTTPStatus

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import ClassVar, List, Optional

from supervisor.graph.graph import SupervisorGraph
from supervisor.models.models import (Any, ErrorResponse, RunCreateStateless,
                                      Union)

router = APIRouter(tags=["Stateless Runs"])
logger = logging.getLogger(__name__)  # This will be "app.api.routes.<name>"
graph = SupervisorGraph()

@router.post(
    "/runs",
    response_model=Any,
    responses={
        "404": {"model": ErrorResponse},
        "409": {"model": ErrorResponse},
        "422": {"model": ErrorResponse},
    },
    tags=["Stateless Runs"],
)
def run_stateless_runs_post(body: RunCreateStateless) -> Union[Any, ErrorResponse]:
    """
    Create Background Run
    """

    try:
        # Extract assistant_id from the payload
        agent_id = body.agent_id
        logging.debug(f"Agent id: {agent_id}")

        # Validate that the assistant_id is not empty.
        if not body.agent_id:
            msg = "agent_id is required and cannot be empty."
            logging.error(msg)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=msg,
            )

        # Retrieve the 'input' field and ensure it is a dictionary.
        input_field = body.input
        if not isinstance(input_field, dict):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Invalid input format"
            )

        # Retrieve the 'query' field from the input dictionary.
        query = input_field.get("query")
        logging.info("query: %s", query)
        result, _ = graph.serve(query)
        print(result)
        logging.info("result: %s", result)
    except HTTPException as http_exc:
        logger.error(
            "HTTP error during run processing: %s", http_exc.detail, exc_info=True
        )
        raise http_exc
    except Exception as exc:
        logger.error("Internal error during run processing: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )

    payload = {
        "agent_id": agent_id,
        "output": result,
        "model": "gpt-4o",
        "metadata": {},
    }

    return JSONResponse(content=payload, status_code=status.HTTP_200_OK)


@router.post(
    "/runs/stream",
    response_model=str,
    responses={
        "404": {"model": ErrorResponse},
        "409": {"model": ErrorResponse},
        "422": {"model": ErrorResponse},
    },
    tags=["Stateless Runs"],
)
def stream_run_stateless_runs_stream_post(
    body: RunCreateStateless,
) -> Union[str, ErrorResponse]:
    """
    Create Run, Stream Output
    """
    pass


@router.post(
    "/runs/wait",
    response_model=Any,
    responses={
        "404": {"model": ErrorResponse},
        "409": {"model": ErrorResponse},
        "422": {"model": ErrorResponse},
    },
    tags=["Stateless Runs"],
)
def wait_run_stateless_runs_wait_post(
    body: RunCreateStateless,
) -> Union[Any, ErrorResponse]:
    """
    Create Background Run
    """
    try:
        # Extract assistant_id from the payload
        agent_id = body.agent_id
        logging.debug(f"Agent id: {agent_id}")

        # Validate that the assistant_id is not empty.
        if not body.agent_id:
            msg = "agent_id is required and cannot be empty."
            logging.error(msg)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=msg,
            )

        # Retrieve the 'input' field and ensure it is a dictionary.
        input_field = body.input
        if not isinstance(input_field, dict):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Invalid input format"
            )

        # Retrieve the 'query' field from the input dictionary.
        query = input_field.get("query")
        logging.info("query: %s", query)
        result, _ = graph.serve(query)
        logging.info("result: %s", result)
    except HTTPException as http_exc:
        logger.error(
            "HTTP error during run processing: %s", http_exc.detail, exc_info=True
        )
        raise http_exc
    except Exception as exc:
        logger.error("Internal error during run processing: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )

    payload = {
        "agent_id": agent_id,
        "output": result,
        "model": "gpt-4o",
        "metadata": {},
    }

    return JSONResponse(content=payload, status_code=status.HTTP_200_OK)

