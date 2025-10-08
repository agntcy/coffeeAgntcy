# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Any
import logging

import asyncio
from mcp.server.fastmcp import FastMCP
import httpx

from agntcy_app_sdk.factory import AgntcyFactory

from config.config import (
    DEFAULT_MESSAGE_TRANSPORT,
    TRANSPORT_SERVER_ENDPOINT,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize a multi-protocol, multi-transport agntcy factory.
factory = AgntcyFactory("lungo_mcp_server", enable_tracing=True)

# Base URLs
NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"

# Create the MCP server
mcp = FastMCP()

HEADERS_NOMINATIM = {
    "User-Agent": "CoffeeAgntcy/1.0"
}

async def make_request(url: str, headers: dict[str, str], params: dict[str, str] = None) -> dict[str, Any] | None:
    """Make a GET request with error handling."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, params=params, timeout=30.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Request error at {url}: {e}")
            return None

async def geocode_location(location: str) -> tuple[float, float] | None:
    """Convert location name to (lat, lon) using Nominatim."""
    params = {
        "q": location,
        "format": "json",
        "limit": "1"
    }
    data = await make_request(NOMINATIM_BASE, headers=HEADERS_NOMINATIM, params=params)
    if data and len(data) > 0:
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return lat, lon
    return None

@mcp.tool()
async def get_forecast(location: str) -> str:
    logging.info(f"Getting weather forecast for location: {location}")
    coords = await geocode_location(location)
    if not coords:
        return f"Could not determine coordinates for location: {location}"
    lat, lon = coords

    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true"
    }

    data = await make_request(OPEN_METEO_BASE, {}, params=params)
    if not data or "current_weather" not in data:
        return f"No weather data available for {location}."

    cw = data["current_weather"]
    return (
        f"Temperature: {cw['temperature']}°C\n"
        f"Wind speed: {cw['windspeed']} m/s\n"
        f"Wind direction: {cw['winddirection']}°"
    )

async def main():
    # serve the MCP server via a message bridge
    transport = factory.create_transport(DEFAULT_MESSAGE_TRANSPORT, endpoint=TRANSPORT_SERVER_ENDPOINT, name="default/default/lungo_weather_service")
    bridge = factory.create_bridge(mcp._mcp_server, transport=transport, topic="lungo_weather_service")
    await bridge.start(blocking=True)

if __name__ == "__main__":
    logging.info("Starting weather service...")
    asyncio.run(main())
