# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""LLM integration test for Colombia weather fallback when Open-Meteo is unavailable."""

from __future__ import annotations

import logging

import pytest

from tests.integration._auction_helpers import (
    AUCTION_PROMPT_CASES,
    TRANSPORT_MATRIX,
    response_has_inventory_amount,
)

logger = logging.getLogger(__name__)

_COLOMBIA_INVENTORY_PROMPT = next(
    c["prompt"] for c in AUCTION_PROMPT_CASES if c["id"] == "colombia_inventory"
)


@pytest.mark.parametrize("transport_config", TRANSPORT_MATRIX, indirect=True)
class TestColombiaWeatherFallback:
    @pytest.mark.agents(["weather-mcp", "colombia-farm"])
    @pytest.mark.open_meteo_stub("error")
    @pytest.mark.use_weather_fallback("true")
    @pytest.mark.usefixtures("agents_up")
    def test_colombia_weather_error_with_fallback_returns_inventory(
        self,
        auction_supervisor_client,
        transport_config,
    ):
        logger.info(
            "\n---Test: colombia weather error with USE_WEATHER_FALLBACK=true "
            f"({transport_config})---"
        )
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": _COLOMBIA_INVENTORY_PROMPT},
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "response" in data
        assert response_has_inventory_amount(data["response"]), (
            "Expected numeric inventory when weather fails but USE_WEATHER_FALLBACK=true"
        )
