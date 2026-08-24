# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.mcp_servers.weather_service."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agents.mcp_servers import weather_service


async def test_get_forecast_colombia_case_insensitive():
    captured = {}

    async def fake_make_request(client, url, headers, params=None):
        captured["params"] = params
        return {
            "current_weather": {
                "temperature": 20.0,
                "windspeed": 1.0,
                "winddirection": 0,
            }
        }

    with patch.object(weather_service, "make_request", side_effect=fake_make_request):
        result = await weather_service.get_forecast("Colombia")

    assert "Temperature: 20.0°C" in result


@pytest.mark.parametrize(
    "case,location,expected_error",
    [
        ("unsupported_brazil", "brazil", ValueError),
        ("unsupported_empty", "  ", ValueError),
    ],
)
async def test_get_forecast_unsupported_location_raises(case, location, expected_error):
    with pytest.raises(expected_error, match="Unsupported location"):
        await weather_service.get_forecast(location)


@pytest.mark.asyncio
async def test_get_forecast_open_meteo_failure_raises():
    with patch.object(weather_service, "make_request", new_callable=AsyncMock, return_value=None):
        with pytest.raises(RuntimeError, match="Failed to retrieve weather data"):
            await weather_service.get_forecast("colombia")


@pytest.mark.asyncio
async def test_get_forecast_missing_current_weather_raises():
    with patch.object(
        weather_service,
        "make_request",
        new_callable=AsyncMock,
        return_value={"daily": {}},
    ):
        with pytest.raises(RuntimeError, match="Failed to retrieve weather data"):
            await weather_service.get_forecast("colombia")


@pytest.mark.asyncio
async def test_get_forecast_success_uses_colombia_coordinates():
    captured = {}

    async def fake_make_request(client, url, headers, params=None):
        captured["params"] = params
        return {
            "current_weather": {
                "temperature": 22.5,
                "windspeed": 3.2,
                "winddirection": 180,
            }
        }

    with patch.object(weather_service, "make_request", side_effect=fake_make_request):
        result = await weather_service.get_forecast("colombia")

    assert captured["params"]["latitude"] == str(weather_service.COLOMBIA_LAT)
    assert captured["params"]["longitude"] == str(weather_service.COLOMBIA_LON)
    assert captured["params"]["windspeed_unit"] == "ms"
    assert "Temperature: 22.5°C" in result
    assert "Wind speed: 3.2 m/s" in result
    assert "Wind direction: 180°" in result
