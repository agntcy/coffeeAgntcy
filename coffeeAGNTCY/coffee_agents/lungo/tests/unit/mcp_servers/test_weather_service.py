# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.mcp_servers.weather_service."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agents.mcp_servers import weather_service

_TEST_LATITUDE = 10.5
_TEST_LONGITUDE = -20.25


@pytest.mark.parametrize(
    "case,latitude,longitude,expected_error",
    [
        ("invalid_latitude_high", 91.0, 0.0, ValueError),
        ("invalid_longitude_high", 0.0, 200.0, ValueError),
        ("invalid_latitude_low", -91.0, 0.0, ValueError),
        ("invalid_longitude_low", 0.0, -181.0, ValueError),
    ],
)
async def test_get_forecast_invalid_coordinates_raises(
    case, latitude, longitude, expected_error
):
    with pytest.raises(expected_error, match="Invalid"):
        await weather_service.get_forecast(latitude, longitude)


@pytest.mark.asyncio
async def test_get_forecast_open_meteo_failure_raises():
    with patch.object(weather_service, "make_request", new_callable=AsyncMock, return_value=None):
        with pytest.raises(RuntimeError, match="Failed to retrieve weather data"):
            await weather_service.get_forecast(_TEST_LATITUDE, _TEST_LONGITUDE)


@pytest.mark.asyncio
async def test_get_forecast_missing_current_weather_raises():
    with patch.object(
        weather_service,
        "make_request",
        new_callable=AsyncMock,
        return_value={"daily": {}},
    ):
        with pytest.raises(RuntimeError, match="Failed to retrieve weather data"):
            await weather_service.get_forecast(_TEST_LATITUDE, _TEST_LONGITUDE)


@pytest.mark.asyncio
async def test_get_forecast_success_passes_coordinates_to_open_meteo():
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
        result = await weather_service.get_forecast(_TEST_LATITUDE, _TEST_LONGITUDE)

    assert captured["params"]["latitude"] == str(_TEST_LATITUDE)
    assert captured["params"]["longitude"] == str(_TEST_LONGITUDE)
    assert captured["params"]["windspeed_unit"] == "ms"
    assert "Temperature: 22.5°C" in result
    assert "Wind speed: 3.2 m/s" in result
    assert "Wind direction: 180°" in result
