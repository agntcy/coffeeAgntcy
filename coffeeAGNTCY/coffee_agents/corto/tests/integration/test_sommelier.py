import logging
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
    @pytest.mark.agents(["farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_sommelier(self, supervisor_client, transport_config):
        logger.info(f"\n---Test: test_sommelier with transport {transport_config}---")
        resp = supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is the flavor of coffee from Brazil?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "response" in data
        max_similarity = 0
        reference_responses = [
        "Brazilian coffee typically has nutty and chocolatey notes, a smooth body, and low acidity.",
        "Expect caramel, cocoa, and a creamy texture from Brazilian coffee, often with a hint of spice.",
        "The flavor profile of Brazilian coffee is characterized by its mildness, often featuring notes of nuts, chocolate, and a pleasant sweetness."
        ]
        for ref_res in reference_responses:
            similarity = get_semantic_similarity(data["response"], ref_res, model)
            if similarity > max_similarity:
                max_similarity = similarity
        expected_min_similarity = 0.75
        print(f"max similarity {max_similarity}")
        assert max_similarity >= expected_min_similarity, \
        f"Agent response '{data["response"]}' did not meet semantic similarity threshold ({expected_min_similarity}) with any reference. Max similarity: {max_similarity}"

