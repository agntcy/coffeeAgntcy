# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""The model the Supply Chain Commitment agents answer with.

The LiteLLM proxy answers an identical request from its cache. Every run of a
case starts with the same request and each later request is built from the
earlier answers, so with the cache on a second run replays the first one word
for word and ten runs are one sample (decisions N33). The agents' replies and
the Buyer's plan are the behaviour under test, so they are asked with the cache
bypassed. Other use cases keep their cache: the setting lives on this model
instance, not in ``common.llm``.
"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI

# LiteLLM proxy request control: do not serve this request from the cache.
NO_CACHE: dict[str, Any] = {"cache": {"no-cache": True}}


def agent_llm(streaming: bool = False) -> Any:
    """The shared model, with the proxy cache bypassed when it is a proxy model."""
    from common.llm import get_llm

    return without_cache(get_llm(streaming=streaming))


def without_cache(llm: Any) -> Any:
    """Add the no-cache control to an OpenAI-compatible (proxy) model.

    Any other model is returned unchanged: without the proxy there is no cache
    to bypass.
    """
    if isinstance(llm, ChatOpenAI):
        llm.extra_body = {**(llm.extra_body or {}), **NO_CACHE}
    return llm
