import re
import pytest
    
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

@pytest.mark.parametrize("transport_config", TRANSPORT_MATRIX, indirect=True)
class TestAuctionFlows:
    @pytest.mark.agents(["brazil-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_brazil_inventory(self, auction_supervisor_client, transport_config):
        print(f"\n---Test: test_auction_brazil_inventory with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is the inventory of coffee in Brazil?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(data)
        assert "response" in data
        assert re.search(r"\b\d+\s*pounds\b", data["response"]), "Expected '<number> pounds' in string"

    @pytest.mark.agents(["weather-mcp", "colombia-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_colombia_inventory(self, auction_supervisor_client, transport_config):
        print(f"\n---Test: test_auction_colombia_inventory with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is the inventory of coffee in Colombia?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(data)
        assert "response" in data
        assert re.search(r'\b[\d,]+\s*(pounds|lbs\.?)\b', data["response"]), "Expected '<number> pounds or <number> lbs.' in string"

    @pytest.mark.agents(["vietnam-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_vietnam_inventory(self, auction_supervisor_client, transport_config):
        print(f"\n---Test: test_auction_vietnam_inventory with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is the inventory of coffee in Vietnam?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(data) 
        assert "response" in data
        assert re.search(r'\b[\d,]+\s*(pounds|lbs\.?)\b', data["response"]), "Expected '<number> pounds or <number> lbs.' in string"


    @pytest.mark.agents(["weather-mcp", "brazil-farm", "colombia-farm", "vietnam-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_all_farms_inventory(self, auction_supervisor_client, transport_config):
        print(f"\n---Test: test_auction_all_farms_inventory with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is the total inventory of coffee across all farms?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(data)
        assert "response" in data
        assert "brazil" in data["response"].lower()
        assert "colombia" in data["response"].lower()
        assert "vietnam" in data["response"].lower()

    @pytest.mark.agents(["brazil-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_create_order_brazil(self, auction_supervisor_client, transport_config):
        print(f"\n---Test: test_auction_create_order_brazil with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "I'd like to buy 200 lbs of coffee at USD 500 price from Brazil."}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(data)
        assert "response" in data
        assert "could not be verified" in data["response"], "Expected verification failure in response"

    @pytest.mark.agents(["weather-mcp","colombia-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_create_order_colombia(self, auction_supervisor_client, transport_config):
        print(f"\n---Test: test_auction_create_order_colombia with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "I'd like to buy 200 lbs of coffee at USD 500 price from Colombia."}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(data)
        assert "response" in data
        assert "successful" in data["response"].lower()
        assert "Order ID" in data["response"], "Expected Order ID in response"
        assert "Tracking Number" in data["response"], "Expected Tracking Number in response"

    @pytest.mark.agents(["vietnam-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_create_order_vietnam(self, auction_supervisor_client, transport_config):
        print(f"\n---Test: test_auction_create_order_vietnam with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "I'd like to buy 200 lbs of coffee at USD 500 price from Vietnam."}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(data)
        assert "successful" in data["response"].lower()
        assert "Order ID" in data["response"], "Expected Order ID in response"
        assert "Tracking Number" in data["response"], "Expected Tracking Number in response"

    @pytest.mark.agents(["brazil-farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_auction_invalid_prompt(self, auction_supervisor_client, transport_config):
        print(f"\n---Test: test_auction_invalid_prompt with transport {transport_config}---")
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is a group of crows called?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(data)
        assert "I'm not sure how to handle that" in data

    @pytest.mark.agents(["logistics-farm", "accountant", "shipper"])
    @pytest.mark.usefixtures("agents_up")
    def test_logistics_order(self, logistics_supervisor_client, transport_config):
        print(f"\n---Test: test_logistics_order with transport {transport_config}---")
        resp = logistics_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "I'd like to order 1000 lbs of coffee from Brazil to be shipped to New York."}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(data)
        assert "response" in data
        assert "Order ID" in data["response"], "Expected Order ID in response"
        assert "Tracking Number" in data["response"], "Expected Tracking Number in response"
