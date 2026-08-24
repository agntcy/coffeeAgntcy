# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for Colombia farm weather validation and fallback policy."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable

from agents.farms.colombia import agent as colombia_agent_module
from agents.farms.colombia.agent import (
    COLOMBIA_LATITUDE,
    COLOMBIA_LONGITUDE,
    FALLBACK_WEATHER_FORECAST,
    FarmAgent,
    _is_valid_weather_forecast,
)


VALID_FORECAST = (
    "Temperature: 18.0°C\n"
    "Wind speed: 2.0 m/s\n"
    "Wind direction: 90°"
)


@pytest.mark.parametrize(
    "case,text,expected",
    [
        ("valid_forecast", VALID_FORECAST, True),
        ("empty", "", False),
        ("whitespace", "   ", False),
        ("error_sentinel_unavailable", "Weather Forecast MCP Server was Unavailable", False),
        ("error_sentinel_no_content", "No content returned from tool.", False),
        ("missing_temperature", "Wind speed: 2.0 m/s", False),
    ],
)
def test_is_valid_weather_forecast(case, text, expected):
    assert _is_valid_weather_forecast(text) is expected


@pytest.fixture
def farm_agent():
    return FarmAgent()


@pytest.mark.asyncio
async def test_get_weather_forecast_valid_mcp_response(farm_agent):
    with patch.object(
        colombia_agent_module,
        "call_mcp_tool",
        new_callable=AsyncMock,
        return_value=VALID_FORECAST,
    ) as mock_call:
        result = await farm_agent._get_weather_forecast({"messages": []})

    mock_call.assert_awaited_once()
    call_kwargs = mock_call.await_args.kwargs
    assert call_kwargs["arguments"] == {
        "latitude": COLOMBIA_LATITUDE,
        "longitude": COLOMBIA_LONGITUDE,
    }
    assert result["weather_forecast_success"] is True
    assert result["weather_forecast"] == VALID_FORECAST


@pytest.mark.asyncio
async def test_get_weather_forecast_invalid_mcp_response(farm_agent):
    with patch.object(
        colombia_agent_module,
        "call_mcp_tool",
        new_callable=AsyncMock,
        return_value="not a valid forecast",
    ):
        result = await farm_agent._get_weather_forecast({"messages": []})

    assert result["weather_forecast_success"] is False
    assert result["weather_forecast"] == ""


@pytest.mark.asyncio
async def test_get_weather_forecast_mcp_exception(farm_agent):
    with patch.object(
        colombia_agent_module,
        "call_mcp_tool",
        new_callable=AsyncMock,
        side_effect=RuntimeError("MCP unavailable"),
    ):
        result = await farm_agent._get_weather_forecast({"messages": []})

    assert result["weather_forecast_success"] is False
    assert result["weather_forecast"] == ""


@pytest.mark.parametrize(
    "case,use_fallback,weather_success,expected_in_prompt,expect_error",
    [
        ("valid_forecast", False, True, VALID_FORECAST, False),
        ("weather_error_strict", False, False, None, True),
        ("weather_error_fallback", True, False, FALLBACK_WEATHER_FORECAST, False),
    ],
)
@pytest.mark.asyncio
async def test_inventory_node_weather_policy(
    farm_agent,
    case,
    use_fallback,
    weather_success,
    expected_in_prompt,
    expect_error,
    monkeypatch,
):
    monkeypatch.setattr(colombia_agent_module, "USE_WEATHER_FALLBACK", use_fallback)

    captured = {}

    class FakeLLM(Runnable):
        def invoke(self, input, config=None, **kwargs):
            captured["prompt_vars"] = input
            return AIMessage(content="5250 lbs")

        async def ainvoke(self, input, config=None, **kwargs):
            return self.invoke(input, config=config, **kwargs)

    farm_agent.inventory_llm = FakeLLM()

    state = {
        "weather_forecast_success": weather_success,
        "weather_forecast": VALID_FORECAST if weather_success else "",
        "messages": [HumanMessage(content="What is the inventory?")],
    }

    result = await farm_agent._inventory_node(state)

    if expect_error:
        assert "Cannot estimate yield" in result["messages"][0].content
        assert "prompt_vars" not in captured
        return

    prompt_text = str(captured["prompt_vars"])
    if case == "weather_error_fallback":
        assert "25.0" in prompt_text
        assert "Conditions: sunny" in prompt_text
    else:
        assert "18.0" in prompt_text
    assert "5250 lbs" in result["messages"][0].content
