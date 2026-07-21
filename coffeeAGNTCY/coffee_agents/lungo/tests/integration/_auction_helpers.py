# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared auction integration helpers for docker and LLM test modules."""

from __future__ import annotations

import json
import re
import ssl
from pathlib import Path

import httpx
import pytest
from huggingface_hub.utils import close_session, set_client_factory
from huggingface_hub.utils._http import default_client_factory
from sentence_transformers import SentenceTransformer, util

TRANSPORT_MATRIX = [
    pytest.param(
        {"DEFAULT_MESSAGE_TRANSPORT": "SLIM", "TRANSPORT_SERVER_ENDPOINT": "http://127.0.0.1:46357"},
        id="SLIM",
    ),
    pytest.param(
        {"DEFAULT_MESSAGE_TRANSPORT": "NATS", "TRANSPORT_SERVER_ENDPOINT": "nats://127.0.0.1:4222"},
        id="NATS",
    ),
]


def response_has_inventory_amount(text: str) -> bool:
    """True if text contains a numeric inventory amount (lbs, pounds, or metric from farms)."""
    return bool(
        re.search(
            r"\b[\d,]+(?:\.\d+)?\s*(pounds|lbs\.?|kg|kilograms?|kilos?)\b",
            text,
            re.IGNORECASE,
        ),
    )


def _unverified_hf_client():
    return httpx.Client(
        verify=ssl._create_unverified_context(),
        follow_redirects=True,
        timeout=httpx.Timeout(60.0, write=60.0),
    )


def _load_sommelier_model():
    """Load SentenceTransformer; use unverified SSL only if first attempt fails with cert error."""
    try:
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        close_session()
        set_client_factory(_unverified_hf_client)
        try:
            model = SentenceTransformer("all-MiniLM-L6-v2")
        finally:
            close_session()
            set_client_factory(default_client_factory)
        return model


_cached_model = None


def get_semantic_similarity(text1, text2):
    global _cached_model
    if _cached_model is None:
        _cached_model = _load_sommelier_model()
    embeddings1 = _cached_model.encode(text1, convert_to_tensor=True)
    embeddings2 = _cached_model.encode(text2, convert_to_tensor=True)
    cosine_score = util.cos_sim(embeddings1, embeddings2)
    return cosine_score.item()


def load_auction_prompt_cases():
    """Load auction prompt cases from JSON in ``tests/integration/``."""
    data_file = Path(__file__).resolve().parent.parent / "integration" / "auction_prompt_cases.json"
    if not data_file.exists():
        raise FileNotFoundError(f"Prompt cases file not found: {data_file}")
    with data_file.open() as f:
        raw = json.load(f)

    cases = raw.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("auction_prompt_cases.json must have a non-empty 'cases' list")

    for case in cases:
        missing = [k for k in ("id", "prompt", "reference_responses") if k not in case]
        if missing:
            raise ValueError(f"Prompt case missing keys {missing}: {case}")
        if not case["reference_responses"]:
            raise ValueError(f"Prompt case '{case['id']}' has empty reference_responses")

    return cases


AUCTION_PROMPT_CASES = load_auction_prompt_cases()
