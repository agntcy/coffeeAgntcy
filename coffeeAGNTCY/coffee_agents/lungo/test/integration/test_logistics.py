import re
import pytest
    
# Reuse the same tests across transports (add/remove configs as needed)
TRANSPORT_MATRIX = [
    pytest.param(
        {"DEFAULT_MESSAGE_TRANSPORT": "SLIM", "TRANSPORT_SERVER_ENDPOINT": "http://127.0.0.1:46357"},
        id="SLIM"
    )
]
@pytest.mark.parametrize("transport_config", TRANSPORT_MATRIX, indirect=True)
class TestAuctionFlows:
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
