# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""LLM integration tests for Colombia weather fallback and strict error paths."""

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from tests.integration._auction_helpers import (
    AUCTION_PROMPT_CASES,
    TRANSPORT_MATRIX,
    response_has_inventory_amount,
)

logger = logging.getLogger(__name__)

_COLOMBIA_INVENTORY_PROMPT = next(
    c["prompt"] for c in AUCTION_PROMPT_CASES if c["id"] == "colombia_inventory"
)


class _FakeStructuredRunnable(Runnable):
    def __init__(self, value):
        self._value = value

    def invoke(self, input, config=None, **kwargs):
        return self._value

    async def ainvoke(self, input, config=None, **kwargs):
        return self._value


class _SupervisorLLMStub(Runnable):
    """Routes to single-farm inventory and echoes farm tool results for formatting."""

    def __init__(self, route: str = "inventory_single_farm"):
        self._route = route

    def invoke(self, input, config=None, **kwargs):
        if isinstance(input, dict) and "tool_result" in input:
            return AIMessage(content=str(input["tool_result"]))
        return AIMessage(content=self._route)

    async def ainvoke(self, input, config=None, **kwargs):
        return self.invoke(input, config=config, **kwargs)

    def with_structured_output(self, schema, **kwargs):
        class ShouldContinue(BaseModel):
            should_continue: bool = Field(default=False)
            reason: str = Field(default="stubbed")

        return _FakeStructuredRunnable(
            schema(should_continue=False, reason="stubbed: no real LLM in this test"),
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

    @pytest.mark.agents(["weather-mcp", "colombia-farm"])
    @pytest.mark.open_meteo_stub("error")
    @pytest.mark.usefixtures("agents_up")
    def test_colombia_weather_error_strict_no_inventory(
        self,
        auction_supervisor_client,
        transport_config,
    ):
        """End-to-end strict mode: Colombia subprocess needs LLM for supervisor routing."""
        logger.info(
            "\n---Test: colombia weather error strict (USE_WEATHER_FALLBACK=false) "
            f"({transport_config})---"
        )
        with patch(
            "agents.supervisors.auction.graph.graph.get_llm",
            return_value=_SupervisorLLMStub(),
        ):
            resp = auction_supervisor_client.post(
                "/agent/prompt",
                json={"prompt": _COLOMBIA_INVENTORY_PROMPT},
            )

        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "response" in data
        assert not response_has_inventory_amount(data["response"]), (
            "Expected no numeric inventory when weather fails and fallback is disabled"
        )
