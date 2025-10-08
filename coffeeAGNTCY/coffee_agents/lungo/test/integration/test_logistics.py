import logging
import pytest

logger = logging.getLogger(__name__)
    
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
    def test_logistics_order(self, logistics_supervisor_client, transport_config):
        logger.info(f"\n---Test: test_logistics_order with transport {transport_config}---")
        resp = logistics_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "I want to order coffee $3.50 per pound for 500 lbs of coffee from the Tatooine farm"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "successfully delivered" in data["response"], "Expected successful delivery message in response"
