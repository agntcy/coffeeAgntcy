# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared A2A ClientConfig construction for supervisor agents (SLIM + optional NATS)."""

from __future__ import annotations

import os

import httpx
from agntcy_app_sdk.semantic.a2a import (
    ClientConfig,
    NatsTransportConfig,
    SlimRpcConfig,
    SlimTransportConfig,
)
from agntcy_app_sdk.transport.slim.transport import SLIMTransport
# The SDK's default SLIM request timeout is 6s, too short for LLM round-trips.
SLIMTransport.request.__defaults__ = (120,)

A2A_HTTP_TIMEOUT = float(os.getenv("A2A_HTTP_TIMEOUT", "120"))

from config.config import NATS_SERVER, SLIM_SERVER


def build_a2a_client_config(
    *,
    namespace: str,
    group: str,
    agent_name: str,
    include_nats: bool = True,
) -> ClientConfig:
    """
    Build ClientConfig for A2AClientFactory using SLIM_SERVER, NATS_SERVER (if enabled),
    and SLIM_SHARED_SECRET from the environment.
    """
    slim_shared_secret = os.getenv("SLIM_SHARED_SECRET")
    if not slim_shared_secret:
        raise ValueError("SLIM_SHARED_SECRET environment variable must be set")

    slimrpc_config = SlimRpcConfig(
        namespace=namespace,
        group=group,
        name=agent_name,
        slim_url=f"http://{SLIM_SERVER}",
        secret=slim_shared_secret,
    )
    slim_config = SlimTransportConfig(
        endpoint=f"http://{SLIM_SERVER}",
        name=f"{namespace}/{group}/{agent_name}",
        shared_secret_identity=slim_shared_secret,
    )
    httpx_client = httpx.AsyncClient(timeout=httpx.Timeout(A2A_HTTP_TIMEOUT))

    if include_nats:
        return ClientConfig(
            httpx_client=httpx_client,
            slimrpc_config=slimrpc_config,
            slim_config=slim_config,
            nats_config=NatsTransportConfig(endpoint=NATS_SERVER),
        )
    return ClientConfig(
        httpx_client=httpx_client,
        slimrpc_config=slimrpc_config,
        slim_config=slim_config,
    )
