# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import re
from pathlib import Path
import pytest

from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)

# Reuse the same tests across transports (add/remove configs as needed)
TRANSPORT_MATRIX = [
    pytest.param(
        {"DEFAULT_MESSAGE_TRANSPORT": "SLIM", "TRANSPORT_SERVER_ENDPOINT": "http://127.0.0.1:46357"},
        id="SLIM"
    ),
    pytest.param(
        {"DEFAULT_MESSAGE_TRANSPORT": "NATS", "TRANSPORT_SERVER_ENDPOINT": "nats://127.0.0.1:4222"},
        id="NATS"
    ),
]

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_semantic_similarity(text1, text2, model):
    embeddings1 = model.encode(text1, convert_to_tensor=True)
    embeddings2 = model.encode(text2, convert_to_tensor=True)
    cosine_score = util.cos_sim(embeddings1, embeddings2)
    return cosine_score.item()


def load_auction_prompt_cases():
    """Load auction prompt cases from JSON.

    Expects a file named 'auction_prompt_cases.json' in this directory with:
      { "cases": [ {"id", "prompt", "reference_responses", "expected_min_similarity"?}, ... ] }
    """
    data_file = Path(__file__).parent / "auction_prompt_cases.json"
    if not data_file.exists():
        raise FileNotFoundError(f"Prompt cases file not found: {data_file}")
    with data_file.open() as f:
        raw = json.load(f)

    cases = raw.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("auction_prompt_cases.json must have a non-empty 'cases' list")

    for c in cases:
        missing = [k for k in ("id", "prompt", "reference_responses") if k not in c]
        if missing:
            raise ValueError(f"Prompt case missing keys {missing}: {c}")
        if not c["reference_responses"]:
            raise ValueError(f"Prompt case '{c['id']}' has empty reference_responses")

    return cases


AUCTION_PROMPT_CASES = load_auction_prompt_cases()

@pytest.mark.parametrize("transport_config", TRANSPORT_MATRIX, indirect=True)
class TestAuctionFlows:
    @pytest.mark.agents(["brazil-farm"])
    @pytest.mark.usefixtures("agents_up")
    @pytest.mark.parametrize(
        "prompt_case",
        [c for c in AUCTION_PROMPT_CASES if c["id"] == "brazil_inventory"],
        ids=["brazil_inventory"],
    )
    def test_auction_brazil_inventory(self, auction_supervisor_client, transport_config, prompt_case):
        logger.info(f"\n---Test: test_auction_brazil_inventory ({prompt_case['id']}) with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": prompt_case["prompt"]}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "response" in data
        assert re.search(r"\b[\d,]+\s*(pounds|lbs\.?)\b", data["response"]), "Expected '<number> pounds or <number> lbs.' in string"

    @pytest.mark.agents(["weather-mcp", "colombia-farm"])
    @pytest.mark.usefixtures("agents_up")
    @pytest.mark.parametrize(
        "prompt_case",
        [c for c in AUCTION_PROMPT_CASES if c["id"] == "colombia_inventory"],
        ids=["colombia_inventory"],
    )
    def test_auction_colombia_inventory(self, auction_supervisor_client, transport_config, prompt_case):
        logger.info(f"\n---Test: test_auction_colombia_inventory ({prompt_case['id']}) with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": prompt_case["prompt"]}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "response" in data
        assert re.search(r'\b[\d,]+\s*(pounds|lbs\.?)\b', data["response"]), "Expected '<number> pounds or <number> lbs.' in string"

    @pytest.mark.agents(["vietnam-farm"])
    @pytest.mark.usefixtures("agents_up")
    @pytest.mark.parametrize(
        "prompt_case",
        [c for c in AUCTION_PROMPT_CASES if c["id"] == "vietnam_inventory"],
        ids=["vietnam_inventory"],
    )
    def test_auction_vietnam_inventory(self, auction_supervisor_client, transport_config, prompt_case):
        logger.info(f"\n---Test: test_auction_vietnam_inventory ({prompt_case['id']}) with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": prompt_case["prompt"]}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data) 
        assert "response" in data
        assert re.search(r'\b[\d,]+\s*(pounds|lbs\.?)\b', data["response"]), "Expected '<number> pounds or <number> lbs.' in string"


    @pytest.mark.agents(["weather-mcp", "brazil-farm", "colombia-farm", "vietnam-farm"])
    @pytest.mark.usefixtures("agents_up")
    @pytest.mark.parametrize(
        "prompt_case",
        [c for c in AUCTION_PROMPT_CASES if c["id"] == "all_farms_yield"],
        ids=["all_farms_yield"],
    )
    def test_auction_all_farms_inventory(self, auction_supervisor_client, transport_config, prompt_case):
        logger.info(f"\n---Test: test_auction_all_farms_inventory ({prompt_case['id']}) with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": prompt_case["prompt"]}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "response" in data
        assert "brazil" in data["response"].lower()
        assert "colombia" in data["response"].lower()
        assert "vietnam" in data["response"].lower()

    @pytest.mark.agents(["brazil-farm"])
    @pytest.mark.usefixtures("agents_up")
    @pytest.mark.parametrize(
        "prompt_case",
        [c for c in AUCTION_PROMPT_CASES if c["id"] == "brazil_create_order"],
        ids=["brazil_create_order"],
    )
    def test_auction_create_order_brazil(self, auction_supervisor_client, transport_config, prompt_case):
        logger.info(
            f"\n---Test: test_auction_create_order_brazil ({prompt_case['id']}) with transport {transport_config}---"
        )
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": prompt_case["prompt"]}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "response" in data
        max_similarity = 0.0
        for ref_res in prompt_case["reference_responses"]:
            similarity = get_semantic_similarity(data["response"], ref_res, model)
            if similarity > max_similarity:
                max_similarity = similarity
        expected_min_similarity = prompt_case.get("expected_min_similarity", 0.75)
        print(f"[{prompt_case['id']}] max similarity {max_similarity}")
        assert max_similarity >= expected_min_similarity, (
            "Agent response did not meet semantic similarity threshold "
            f"({expected_min_similarity}). Max similarity: {max_similarity}. "
            f"Prompt: {prompt_case['prompt']!r}. Response: {data['response']!r}"
        )

    @pytest.mark.agents(["weather-mcp","colombia-farm"])
    @pytest.mark.usefixtures("agents_up")
    @pytest.mark.parametrize(
        "prompt_case",
        [c for c in AUCTION_PROMPT_CASES if c["id"] == "colombia_create_order"],
        ids=["colombia_create_order"],
    )
    def test_auction_create_order_colombia(self, auction_supervisor_client, transport_config, prompt_case):
        logger.info(f"\n---Test: test_auction_create_order_colombia ({prompt_case['id']}) with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": prompt_case["prompt"]}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "response" in data
        assert "successful" in data["response"].lower()
        assert "Order ID" in data["response"], "Expected Order ID in response"
        assert "Tracking Number" in data["response"], "Expected Tracking Number in response"
        # Success flow: rely on structural checks only; no semantic similarity enforcement

    @pytest.mark.agents(["vietnam-farm"])
    @pytest.mark.usefixtures("agents_up")
    @pytest.mark.parametrize(
        "prompt_case",
        [c for c in AUCTION_PROMPT_CASES if c["id"] == "vietnam_create_order"],
        ids=["vietnam_create_order"],
    )
    def test_auction_create_order_vietnam(self, auction_supervisor_client, transport_config, prompt_case):
        logger.info(f"\n---Test: test_auction_create_order_vietnam ({prompt_case['id']}) with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": prompt_case["prompt"]}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "successful" in data["response"].lower()
        assert "Order ID" in data["response"], "Expected Order ID in response"
        assert "Tracking Number" in data["response"], "Expected Tracking Number in response"

    @pytest.mark.agents(["brazil-farm"])
    @pytest.mark.usefixtures("agents_up")
    @pytest.mark.parametrize(
        "prompt_case",
        [c for c in AUCTION_PROMPT_CASES if c["id"] == "invalid_prompt"],
        ids=["invalid_prompt"],
    )
    def test_auction_invalid_prompt(self, auction_supervisor_client, transport_config, prompt_case):
        logger.info(f"\n---Test: test_auction_invalid_prompt ({prompt_case['id']}) with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": prompt_case["prompt"]}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "I'm not sure how to handle that" in data["response"]

    