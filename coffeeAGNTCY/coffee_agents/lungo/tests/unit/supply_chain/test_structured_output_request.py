# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""What the real clients put on the wire for the supply chain models.

The fake LLM tests show that the call sites pass ``strict=True``. They cannot
show that the client then sends it: ``langchain-openai`` and
``langchain-litellm`` each build the request in their own way, and a version
change could drop ``strict`` or the all-required schema without any error. A
stub server records the request body that each client sends, on the proxy
path (``ChatOpenAI``) and on the Azure path (``ChatLiteLLM``).
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from langchain_core.messages import HumanMessage
from langchain_litellm import ChatLiteLLM
from langchain_openai import ChatOpenAI

from agents.supervisors.supply_chain.selection import _Extracted
from agents.supervisors.supply_chain.strategies.baseline import BuyerDecision
from agents.supply_chain.common.member import ConfirmDecision
from tests.helpers.supply_chain_schemas import strict_violations

# A valid answer for each model, so that the client parses it like a real one.
ANSWERS = {
    _Extracted: {"case": None, "configuration": None},
    ConfirmDecision: {"decision": "confirm", "reason": "ok"},
    BuyerDecision: {"action": "withhold", "message": "", "plan": None, "reason": "x"},
}


class _Stub:
    """A local chat completions endpoint that records each request body."""

    def __init__(self) -> None:
        self.bodies: list[dict] = []
        self.answer: dict = {}
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("content-length", 0))
                stub.bodies.append(json.loads(self.rfile.read(length)))
                payload = json.dumps(
                    {
                        "id": "stub",
                        "object": "chat.completion",
                        "created": 0,
                        "model": "gpt-4o",
                        "choices": [
                            {
                                "index": 0,
                                "finish_reason": "stop",
                                "message": {
                                    "role": "assistant",
                                    "content": json.dumps(stub.answer),
                                },
                            }
                        ],
                        "usage": {
                            "prompt_tokens": 1,
                            "completion_tokens": 1,
                            "total_tokens": 2,
                        },
                    }
                ).encode()
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *_args):
                pass

        self._server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._server.server_port}"
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture
def stub():
    server = _Stub()
    yield server
    server.close()


def _proxy_llm(url: str):
    """The LiteLLM proxy path of ``common.llm.get_llm``."""
    return ChatOpenAI(base_url=url, model="gpt-4o", api_key="key", streaming=False)


def _azure_llm(url: str):
    """The Azure path of ``common.llm.get_llm``."""
    return ChatLiteLLM(
        model="azure/gpt-4o", api_base=url, api_key="key", api_version="2024-10-21"
    )


@pytest.mark.parametrize("make_llm", [_proxy_llm, _azure_llm], ids=["proxy", "azure"])
@pytest.mark.parametrize("model", list(ANSWERS), ids=lambda m: m.__name__)
async def test_the_request_asks_for_a_strict_valid_schema(stub, make_llm, model):
    stub.answer = ANSWERS[model]

    structured = make_llm(stub.url).with_structured_output(model, strict=True)
    result = await structured.ainvoke([HumanMessage("hello")])

    assert isinstance(result, model)
    (body,) = stub.bodies
    response_format = body["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert strict_violations(response_format["json_schema"]["schema"]) == []
