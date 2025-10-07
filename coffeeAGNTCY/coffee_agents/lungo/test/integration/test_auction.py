import pytest

# from test.integration.mocks.mock_llm import MockLangChainLLM

# def test_get_llm_uses_mock():
#     llm = get_llm()
#     out = llm.invoke("Tell me about Colombia").content
#     assert "Colombia farm inventory has 500 lb." in out  # proves the mock is used, not Azure
    
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
    @pytest.mark.parametrize("farm_up", ["brazil"], indirect=True)
    # @pytest.mark.usefixtures("brazil_farm_up")  # add colombia/vietnam as needed
    def test_auction_brazil_inventory(
        self,
        farm_up,
        auction_supervisor_client,
        # mock_llm_instance: MockLangChainLLM,
        transport_config
        ):
        print(f"\n---Test: test_auction_brazil_inventory with transport {transport_config}---")

        # mock_llm_instance.set_mock_responses({
        #     "What is the inventory of coffee in Brazil?": "Brazil farm inventory includes 20 lb.",
        #     "You are an inventory broker for a global coffee exchange company.": 
        # })

        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is the inventory of coffee in Brazil?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(data)
        assert "response" in data
        # Optional: check content is sensible (tighten once flows are deterministic)
        # assert "Brazil" in data["response"]

        # Optional: verify LLM got some prompt; loosen/tighten as your graph evolves
        # assert any("Brazil" in p for p in mock_llm_factory_patch.call_history)

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