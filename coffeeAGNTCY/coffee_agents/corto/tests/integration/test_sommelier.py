# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
import json
import logging
from typing import Any, Dict, List
import pytest
from pathlib import Path
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

def load_prompt_cases() -> List[Dict[str, Any]]:
    data_file = Path(__file__).parent / "prompt_cases.json"
    if not data_file.exists():
        raise FileNotFoundError(f"Prompt cases file not found: {data_file}")
    with data_file.open() as f:
        raw = json.load(f)

    cases = raw.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("prompt_cases.json must have a non-empty 'cases' list")

    for c in cases:
        missing = [k for k in ("id", "prompt", "reference_responses") if k not in c]
        if missing:
            raise ValueError(f"Prompt case missing keys {missing}: {c}")
        if not c["reference_responses"]:
            raise ValueError(f"Prompt case '{c['id']}' has empty reference_responses")

    return cases



PROMPT_CASES = load_prompt_cases()

@pytest.mark.parametrize("transport_config", TRANSPORT_MATRIX, indirect=True)
@pytest.mark.parametrize("prompt_case", PROMPT_CASES, ids=[c["id"] for c in PROMPT_CASES])
class TestAuctionFlows:
    @pytest.mark.agents(["farm"])
    @pytest.mark.usefixtures("agents_up")
    def test_sommelier(self, supervisor_client, transport_config, prompt_case):
        logger.info(f"\n---Test: test_sommelier with {prompt_case['id']} and transport {transport_config}---")
        resp = supervisor_client.post(
            "/agent/prompt",
            json={"prompt": prompt_case["prompt"]}
        )
        assert resp.status_code == 200
        data = resp.json()
        logger.info(data)
        assert "response" in data
        max_similarity = 0
        for ref_res in prompt_case["reference_responses"]:
            similarity = get_semantic_similarity(data["response"], ref_res, model)
            if similarity > max_similarity:
                max_similarity = similarity
        expected_min_similarity = prompt_case.get("expected_min_similarity", 0.75)
        print(f"[{prompt_case['id']}] max similarity {max_similarity}")
        assert max_similarity >= expected_min_similarity, (
            f"Response did not meet similarity threshold {expected_min_similarity}. "
            f"Got {max_similarity} for prompt '{prompt_case['prompt']}'."
        )