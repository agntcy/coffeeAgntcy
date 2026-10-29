# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""The agents bypass the proxy cache; other models are left alone (decisions N33)."""

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from agents.supply_chain.common.llm import NO_CACHE, agent_llm, without_cache


def _proxy_model(**kwargs) -> ChatOpenAI:
    return ChatOpenAI(model="m", api_key="k", base_url="http://localhost:1", **kwargs)


def test_a_proxy_model_asks_the_proxy_not_to_use_its_cache():
    model = without_cache(_proxy_model())
    payload = model._get_request_payload([HumanMessage("hi")])
    assert payload["extra_body"] == NO_CACHE


def test_other_request_options_are_kept():
    model = without_cache(_proxy_model(extra_body={"metadata": {"a": 1}}))
    assert model.extra_body == {"metadata": {"a": 1}, **NO_CACHE}


def test_a_model_that_is_not_a_proxy_model_is_returned_unchanged():
    class Other:
        pass

    other = Other()
    assert without_cache(other) is other
    assert not hasattr(other, "extra_body")


def test_the_agents_get_the_shared_model_without_its_cache(monkeypatch):
    import common.llm as shared

    monkeypatch.setattr(shared, "get_llm", lambda streaming=True: _proxy_model())
    model = agent_llm()
    assert model.extra_body == NO_CACHE
