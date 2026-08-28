# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Docker integration tests for weather MCP + Open-Meteo stub (no LLM)."""

from __future__ import annotations

import logging

import pytest

from agents.farms.colombia.agent import (
    COLOMBIA_LATITUDE,
    COLOMBIA_LONGITUDE,
    _is_valid_weather_forecast,
)
from common.stable_agent_id import stable_agent_id_for_name
from tests.integration._auction_helpers import TRANSPORT_MATRIX

logger = logging.getLogger(__name__)

_WEATHER_MCP_ARGS = {
    "topic": "lungo_weather_service",
    "tool_name": "get_forecast",
    "arguments": {
        "latitude": COLOMBIA_LATITUDE,
        "longitude": COLOMBIA_LONGITUDE,
    },
    "agent_id": "Colombia Coffee Farm",
    "source": "colombia_coffee_farm",
    "target_stable_agent_id": stable_agent_id_for_name("Weather MCP Server"),
    "message_timeout": 45,
    "list_tools_first": True,
    "extract_text": True,
}


@pytest.mark.parametrize(
    "transport_config",
    [TRANSPORT_MATRIX[0]],
    indirect=True,
)
@pytest.mark.agents(["weather-mcp"])
@pytest.mark.open_meteo_stub("error")
@pytest.mark.usefixtures("agents_up")
async def test_weather_mcp_open_meteo_stub_error_is_not_valid_forecast(
    transport_config,
    loopback_mcp_client,
):
    """Weather MCP subprocess with failing Open-Meteo stub must not return forecast text."""
    logger.info(
        "\n---Test: weather-mcp Open-Meteo stub error (%s)---",
        transport_config,
    )
    try:
        result = await loopback_mcp_client(**_WEATHER_MCP_ARGS)
    except Exception:
        return

    assert not _is_valid_weather_forecast(str(result)), (
        f"Expected invalid forecast text from failing stub, got: {result!r}"
    )


@pytest.mark.parametrize(
    "transport_config",
    [TRANSPORT_MATRIX[0]],
    indirect=True,
)
@pytest.mark.agents(["weather-mcp"])
@pytest.mark.usefixtures("agents_up")
async def test_weather_mcp_open_meteo_stub_success_returns_forecast(
    transport_config,
    loopback_mcp_client,
):
    """Weather MCP subprocess with success stub returns parseable forecast text."""
    logger.info(
        "\n---Test: weather-mcp Open-Meteo stub success (%s)---",
        transport_config,
    )
    result = await loopback_mcp_client(**_WEATHER_MCP_ARGS)

    assert _is_valid_weather_forecast(result), f"Expected valid forecast text, got: {result!r}"
    assert "22.0" in result
