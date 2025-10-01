from common.llm import get_llm
import pytest

def test_get_llm_uses_mock():
    llm = get_llm()
    out = llm.invoke("Tell me about Colombia").content
    assert "Colombia farm inventory has 500 lb." in out  # proves the mock is used, not Azure
    
# Reuse the same tests across transports (add/remove configs as needed)
TRANSPORT_MATRIX = [
    pytest.param(
        {"DEFAULT_MESSAGE_TRANSPORT": "SLIM", "TRANSPORT_SERVER_ENDPOINT": "http://127.0.0.1:46357"},
        id="SLIM"
    ),
    # pytest.param(
    #     {"DEFAULT_MESSAGE_TRANSPORT": "NATS", "TRANSPORT_SERVER_ENDPOINT": "nats://0.0.0.0:4222"},
    #     id="NATS"
    # ),
]

@pytest.mark.parametrize("transport_config", TRANSPORT_MATRIX, indirect=True)
class TestAuctionFlows:
    @pytest.mark.usefixtures("brazil_farm_up")  # add colombia/vietnam as needed
    def test_auction_colombia_inventory(self, auction_supervisor_client, mock_llm_factory_patch):
        """
        End-to-end: supervisor -> transports -> Colombia farm.
        """
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is the inventory of coffee in Colombia?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        # Optional: check content is sensible (tighten once flows are deterministic)
        # assert "Colombia" in data["response"]

        # Optional: verify LLM got some prompt; loosen/tighten as your graph evolves
        assert any("Colombia" in p for p in mock_llm_client_patch.call_history)

    # def test_auction_vietnam_inventory(self, auction_supervisor_client, mock_llm_client_patch):
    #     resp = auction_supervisor_client.post(
    #         "/agent/prompt",
    #         json={"prompt": "What is the inventory of coffee in Vietnam?"}
    #     )
    #     assert resp.status_code == 200
    #     data = resp.json()
    #     assert "response" in data
    #     assert any("Vietnam" in p for p in mock_llm_client_patch.call_history)

    # def test_auction_brazil_inventory(self, auction_supervisor_client, mock_llm_client_patch):
    #     resp = auction_supervisor_client.post(
    #         "/agent/prompt",
    #         json={"prompt": "What is the inventory of coffee in Brazil?"}
    #     )
    #     assert resp.status_code == 200
    #     data = resp.json()
    #     assert "response" in data
    #     assert any("Brazil" in p for p in mock_llm_client_patch.call_history)