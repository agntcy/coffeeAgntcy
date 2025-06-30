import argparse
from typing import Any

import httpx
import uvicorn

from mcp.server.fastmcp import FastMCP

# Base URLs
NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"

# Create the MCP server
mcp = FastMCP()

# Standard request headers
HEADERS_NWS = {
    "Accept": "application/geo+json",
    "User-Agent": "ColombiaCoffeeFarmAgent/1.0"
}

HEADERS_NOMINATIM = {
    "User-Agent": "ColombiaCoffeeFarmAgent/1.0"
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

if __name__ == "__main__":
    app = mcp.streamable_http_app()
    for route in app.routes:
        print(f"{route.path} ")
    uvicorn.run(mcp.streamable_http_app, host="localhost", port=8123)
