# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from pathlib import Path
import pytest

logger = logging.getLogger(__name__)
 
def load_logistics_prompt_cases():
    """Load logistics prompt cases from JSON in this directory.

        Expected schema:
            { "cases": [ {"id", "prompt"}, ... ] }
    """
    data_file = Path(__file__).parent / "logistics_prompt_cases.json"
    if not data_file.exists():
        raise FileNotFoundError(f"Prompt cases file not found: {data_file}")
    with data_file.open() as f:
        raw = json.load(f)

    cases = raw.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("logistics_prompt_cases.json must have a non-empty 'cases' list")

    for c in cases:
        missing = [k for k in ("id", "prompt") if k not in c]
        if missing:
            raise ValueError(f"Prompt case missing keys {missing}: {c}")

    return cases

LOGISTICS_PROMPT_CASES = load_logistics_prompt_cases()
    
# Reuse the same tests across transports (add/remove configs as needed)
TRANSPORT_MATRIX = [
    pytest.param(
        {"DEFAULT_MESSAGE_TRANSPORT": "SLIM", "TRANSPORT_SERVER_ENDPOINT": "http://127.0.0.1:46357"},
        id="SLIM"
    )
]

@pytest.mark.parametrize("transport_config", TRANSPORT_MATRIX, indirect=True)
class TestLogisticsFlows:
    @pytest.mark.agents(["logistics-farm", "accountant", "shipper"])
    @pytest.mark.usefixtures("agents_up")
    @pytest.mark.parametrize(
        "prompt_case",
        [c for c in LOGISTICS_PROMPT_CASES if c["id"] == "logistics_order"],
        ids=["logistics_order"],
    )
    def test_logistics_order(self, logistics_supervisor_client, transport_config, prompt_case):
        logger.info(f"\n---Test: test_logistics_order ({prompt_case['id']}) with transport {transport_config}---")
        resp = logistics_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": prompt_case["prompt"]}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "successfully delivered" in data["response"], "Expected successful delivery message in response"
