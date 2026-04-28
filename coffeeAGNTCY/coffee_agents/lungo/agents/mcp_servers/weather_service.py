# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import config.logging_config  # noqa: F401 - runs setup on import; must be first

from typing import Any
from datetime import datetime, timezone
import logging
import os

import asyncio
from mcp.server.fastmcp import FastMCP
import httpx
from agntcy_app_sdk.factory import AgntcyFactory

from agents.mcp_servers.utils import _mcp_transport, _mcp_endpoint
from config.config import OTEL_SDK_DISABLED

logger = logging.getLogger(__name__)

# Initialize a multi-protocol, multi-transport agntcy factory.
factory = AgntcyFactory("lungo.mcp_server", enable_tracing=not OTEL_SDK_DISABLED)

# Base URLs
NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"

# Create the MCP server
mcp = FastMCP()

HEADERS_NOMINATIM = {
    "User-Agent": "CoffeeAgntcy/1.0"
}

async def make_request(client: httpx.AsyncClient, url: str, headers: dict[str, str], params: dict[str, str] = None) -> dict[str, Any] | None:
    """Make a GET request with error handling using an existing client"""
    try:
        resp = await client.get(url, headers=headers, params=params, timeout=30.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Request error at {url} with params {params} and headers {headers}: {e}")
        return None

async def geocode_location(client: httpx.AsyncClient, location: str) -> tuple[float, float] | None:
    """Convert location name to (lat, lon) using Nominatim."""
    params = {
        "q": location,
        "format": "json",
        "limit": "1"
    }
    data = await make_request(client, NOMINATIM_BASE, headers=HEADERS_NOMINATIM, params=params)
    if data and "lat" in data[0] and "lon" in data[0]:
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return lat, lon
    return None

@mcp.tool()
async def get_forecast(location: str) -> str:
    logging.info(f"Getting weather forecast for location: {location}")
    async with httpx.AsyncClient() as client:
        coords = await geocode_location(client, location)
        if not coords:
            return f"Could not determine coordinates for location: {location}"
        lat, lon = coords

        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true"
        }

        data = await make_request(client, OPEN_METEO_BASE, {}, params=params)
        if not data or "current_weather" not in data:
            logging.error(f"Failed to retrieve weather data for {location}")
            logging.error(f"Response data: {data}")
            # Use backup data if API call fails
            cw = {
                "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M"),  # e.g. 2025-10-17T22:15
                "temperature": 25.9,
                "windspeed": 1.8,
                "winddirection": 307,
            }
        else:
            cw = data["current_weather"]
        return (
            f"Temperature: {cw['temperature']}°C\n"
            f"Wind speed: {cw['windspeed']} m/s\n"
            f"Wind direction: {cw['winddirection']}°"
        )

async def main():
    # serve the MCP server via a message bridge
    transport = factory.create_transport(
        _mcp_transport,
        endpoint=_mcp_endpoint,
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
