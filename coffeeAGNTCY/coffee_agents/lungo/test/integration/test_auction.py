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
    @pytest.mark.farms(["brazil"])
    @pytest.mark.usefixtures("farms_up")
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

    @pytest.mark.usefixtures("start_weather_mcp")
    @pytest.mark.farms(["colombia"])
    @pytest.mark.usefixtures("farms_up")
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
    

    @pytest.mark.farms(["vietnam"])
    @pytest.mark.usefixtures("farms_up")
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
    
    @pytest.mark.farms(["brazil", "colombia", "vietnam"])
    @pytest.mark.usefixtures("farms_up")
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
       