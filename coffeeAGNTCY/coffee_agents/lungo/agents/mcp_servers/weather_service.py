# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import config.logging_config  # noqa: F401 - runs setup on import; must be first

from typing import Any
import logging
import os

import asyncio
from mcp.server.fastmcp import FastMCP
import httpx
from agntcy_app_sdk.factory import AgntcyFactory

from common.mcp_client import mcp_transport, mcp_endpoint
from config.config import OTEL_SDK_DISABLED

logger = logging.getLogger(__name__)

# Initialize a multi-protocol, multi-transport agntcy factory.
factory = AgntcyFactory("lungo.mcp_server", enable_tracing=not OTEL_SDK_DISABLED)

OPEN_METEO_BASE = os.getenv(
    "OPEN_METEO_BASE",
    "https://api.open-meteo.com/v1/forecast",
)

COLOMBIA_LAT = 4.0999170
COLOMBIA_LON = -72.9088133

# Create the MCP server
mcp = FastMCP()


async def make_request(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    params: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Make a GET request with error handling using an existing client."""
    try:
        resp = await client.get(url, headers=headers, params=params, timeout=30.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(
            "Request error at %s with params %s and headers %s: %s",
            url,
            params,
            headers,
            e,
        )
        return None


@mcp.tool()
async def get_forecast(location: str) -> str:
    logging.info("Getting weather forecast for location: %s", location)
    normalized = location.strip().lower()
    if normalized != "colombia":
        raise ValueError(f"Unsupported location: {location!r}")

    async with httpx.AsyncClient() as client:
        params = {
            "latitude": str(COLOMBIA_LAT),
            "longitude": str(COLOMBIA_LON),
            "current_weather": "true",
            "windspeed_unit": "ms",
        }

        data = await make_request(client, OPEN_METEO_BASE, {}, params=params)
        if not data or "current_weather" not in data:
            logging.error("Failed to retrieve weather data for %s", location)
            logging.error("Response data: %s", data)
            raise RuntimeError(f"Failed to retrieve weather data for {location}")

        cw = data["current_weather"]
        return (
            f"Temperature: {cw['temperature']}°C\n"
            f"Wind speed: {cw['windspeed']} m/s\n"
            f"Wind direction: {cw['winddirection']}°"
        )


async def main():
    # serve the MCP server via a message bridge
    transport = factory.create_transport(
        mcp_transport,
        endpoint=mcp_endpoint,
        shared_secret_identity=os.getenv("SLIM_SHARED_SECRET"),
        name="default/default/lungo_weather_service")

    app_session = factory.create_app_session()
    app_session \
        .add(mcp._mcp_server) \
        .with_transport(transport) \
        .with_topic("lungo_weather_service") \
        .with_session_id("default_session").build()

    await app_session.start_all_sessions(keep_alive=False)
    logger.info("Agent ready")
    await app_session.start_all_sessions(keep_alive=True)

if __name__ == "__main__":
    logging.info("Starting weather service...")
    asyncio.run(main())
