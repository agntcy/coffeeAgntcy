# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
import re
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

@pytest.mark.parametrize("transport_config", TRANSPORT_MATRIX, indirect=True)
class TestAuctionFlows:
    @pytest.mark.agents(["brazil-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_brazil_inventory(self, auction_supervisor_client, transport_config):
        logger.info(f"\n---Test: test_auction_brazil_inventory with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is the inventory of coffee in Brazil?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "response" in data
        assert re.search(r"\b\d+\s*pounds\b", data["response"]), "Expected '<number> pounds' in string"

    @pytest.mark.agents(["weather-mcp", "colombia-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_colombia_inventory(self, auction_supervisor_client, transport_config):
        logger.info(f"\n---Test: test_auction_colombia_inventory with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is the inventory of coffee in the Colombia farm?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "response" in data
        assert re.search(r'\b[\d,]+\s*(pounds|lbs\.?)\b', data["response"]), "Expected '<number> pounds or <number> lbs.' in string"

    @pytest.mark.agents(["vietnam-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_vietnam_inventory(self, auction_supervisor_client, transport_config):
        logger.info(f"\n---Test: test_auction_vietnam_inventory with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is the inventory of coffee in Vietnam?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data) 
        assert "response" in data
        assert re.search(r'\b[\d,]+\s*(pounds|lbs\.?)\b', data["response"]), "Expected '<number> pounds or <number> lbs.' in string"


    @pytest.mark.agents(["weather-mcp", "brazil-farm", "colombia-farm", "vietnam-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_all_farms_inventory(self, auction_supervisor_client, transport_config):
        logger.info(f"\n---Test: test_auction_all_farms_inventory with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is the total inventory of coffee across all farms?"}
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
    def test_auction_create_order_brazil(self, auction_supervisor_client, transport_config):
        logger.info(f"\n---Test: test_auction_create_order_brazil with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "I'd like to buy 200 lbs of coffee at USD 500 price from Brazil."}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "response" in data
        max_similarity = 0
        reference_responses = [
        "Unfortunately, I cannot process orders from Brazil at this time due to logistical constraints.",
        "I'm sorry, I was unable to complete your order request for all items. An issue occurred for some parts. Please try again later.",
        "Regrettably, I am unable to fulfill orders from Brazil currently due to supply chain issues."
        "I encountered some issues retrieving information for your request. Some parts could not be completed at this time due to a technical issue. Please try again later.",
        "The user's request to buy coffee could not be processed due to an identity verification error with the farm. The conversation cannot proceed without resolving this issue, and the user has not provided any further instructions or questions.",
        "I'm sorry, I was unable to complete your order request for all items. An issue occurred for some parts. Please try again later."
        ]
        for ref_res in reference_responses:
            similarity = get_semantic_similarity(data["response"], ref_res, model)
            if similarity > max_similarity:
                max_similarity = similarity
        expected_min_similarity = 0.75
        print(f"max similarity {max_similarity}")
        assert max_similarity >= expected_min_similarity, \
        f"Agent response '{data["response"]}' did not meet semantic similarity threshold ({expected_min_similarity}) with any reference. Max similarity: {max_similarity}"

    @pytest.mark.agents(["weather-mcp","colombia-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_create_order_colombia(self, auction_supervisor_client, transport_config):
        logger.info(f"\n---Test: test_auction_create_order_colombia with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "I'd like to buy 200 lbs of coffee at USD 500 price from Colombia."}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "response" in data
        assert "successful" in data["response"].lower()
        assert "Order ID" in data["response"], "Expected Order ID in response"
        assert "Tracking Number" in data["response"], "Expected Tracking Number in response"

    @pytest.mark.agents(["vietnam-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_create_order_vietnam(self, auction_supervisor_client, transport_config):
        logger.info(f"\n---Test: test_auction_create_order_vietnam with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "I'd like to buy 200 lbs of coffee at USD 500 price from Vietnam."}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "successful" in data["response"].lower()
        assert "Order ID" in data["response"], "Expected Order ID in response"
        assert "Tracking Number" in data["response"], "Expected Tracking Number in response"

    @pytest.mark.agents(["brazil-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_invalid_prompt(self, auction_supervisor_client, transport_config):
        logger.info(f"\n---Test: test_auction_invalid_prompt with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is a group of crows called?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "I'm not sure how to handle that" in data["response"]

    