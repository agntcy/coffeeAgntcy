import argparse
from typing import Any

import httpx
import uvicorn

from mcp.server.fastmcp import FastMCP

# Base URLs
NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"
NWS_BASE = "https://api.weather.gov"

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
    """Get weather forecast for a given location name using NWS."""
    coords = await geocode_location(location)
    if not coords:
        return f"Could not determine coordinates for location: {location}"

    lat, lon = coords
    points_url = f"{NWS_BASE}/points/{lat},{lon}"
    points_data = await make_request(points_url, headers=HEADERS_NWS)

    if not points_data or "properties" not in points_data or "forecast" not in points_data["properties"]:
        return f"Could not get forecast URL for coordinates {lat}, {lon}"

    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_request(forecast_url, headers=HEADERS_NWS)

    if not forecast_data or "properties" not in forecast_data or "periods" not in forecast_data["properties"]:
        return f"Could not get forecast data for {location}"

    current = forecast_data["properties"]["periods"][0]

    result = (
        f"{current['name']}:\n"
        f"Temperature: {current['temperature']}°{current['temperatureUnit']}\n"
        f"Wind: {current['windSpeed']} {current['windDirection']}\n"
        f"Forecast: {current['detailedForecast']}"
    )

    return result

if __name__ == "__main__":
    uvicorn.run(mcp.streamable_http_app, host="localhost", port=8123)
