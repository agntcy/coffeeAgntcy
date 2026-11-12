# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the A2A client side of the recruiter (a2a-sdk 1.x).

Covers record parsing, the task callback, the remote agent connection (against
the in-process recruiter app) and the evaluator's response handling.
"""

import json
from uuid import uuid4

import httpx
import pytest
from a2a.client import ClientConfig, ClientFactory
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCard,
    AgentInterface,
    Artifact,
    Message,
    Role,
    StreamResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from starlette.applications import Starlette

from agent_recruiter.common.a2a_helpers import (
    data_part,
    part_data,
    parts_text,
    text_part,
    to_struct,
)
from agent_recruiter.interviewers.a2a.a2a_evaluator_agent import (
    A2AEvaluatorAgent,
    ensure_jsonrpc_interface,
)
from agent_recruiter.interviewers.a2a.generic_task_callback import (
    GenericTaskUpdateCallback,
)
from agent_recruiter.interviewers.a2a.record_parser import parse_a2a_agent_record
from agent_recruiter.interviewers.a2a.remote_agent_connection import (
    RemoteAgentConnections,
)
from agent_recruiter.server.app import build_app
from agent_recruiter.server.card import AGENT_CARD

import agent_recruiter.server.agent_executor as executor_module
from tests.unit.test_a2a_server import FakeTeam, FOUND_RECORDS

V03_CARD = {
    "name": "Legacy Agent",
    "description": "A v0.3 card",
    "url": "http://legacy.example:9000",
    "version": "1.0.0",
    "protocolVersion": "0.3.0",
    "preferredTransport": "JSONRPC",
    "capabilities": {"streaming": True},
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
    "skills": [],
}


class TestParseRecord:
    def test_v03_card_uses_its_url(self):
        config = parse_a2a_agent_record(V03_CARD)

        assert config.evaluated_agent_url == "http://legacy.example:9000"
        assert config.agent_name == "Legacy Agent"

    def test_v03_card_as_json_string(self):
        config = parse_a2a_agent_record(json.dumps(V03_CARD))

        assert config.evaluated_agent_url == "http://legacy.example:9000"

    def test_v03_additional_interface_is_not_preferred_over_the_main_one(self):
        record = {
            **V03_CARD,
            "additionalInterfaces": [
                {"transport": "GRPC", "url": "grpc://legacy.example:9001"}
            ],
        }

        assert (
            parse_a2a_agent_record(record).evaluated_agent_url
            == "http://legacy.example:9000"
        )

    def test_v1_card_prefers_the_jsonrpc_interface(self):
        record = {
            "name": "Modern Agent",
            "description": "A v1 card",
            "supportedInterfaces": [
                {
                    "url": "slim://slim:46357/agent",
                    "protocolBinding": "slimpatterns",
                    "protocolVersion": "1.0",
                },
                {
                    "url": "http://modern.example:9000",
                    "protocolBinding": "JSONRPC",
                    "protocolVersion": "1.0",
                },
            ],
        }

        assert (
            parse_a2a_agent_record(record).evaluated_agent_url
            == "http://modern.example:9000"
        )

    def test_loose_directory_record_with_only_name_and_url(self):
        config = parse_a2a_agent_record({"name": "Loose", "url": "http://loose:1"})

        assert config.evaluated_agent_url == "http://loose:1"

    def test_record_without_a_url_is_rejected(self):
        with pytest.raises(ValueError, match="missing a 'url'"):
            parse_a2a_agent_record({"name": "No URL"})

    def test_record_without_a_name_gets_the_default_name(self):
        config = parse_a2a_agent_record({"url": "http://nameless:1"})

        assert config.agent_name == "Unknown"
        assert config.evaluated_agent_url == "http://nameless:1"

    def test_a_record_that_is_not_a_dict_raises_value_error(self):
        # The fallback error path used to read a variable that Python had
        # already deleted, which raised UnboundLocalError instead.
        with pytest.raises(ValueError, match="Could not parse agent record"):
            parse_a2a_agent_record([1, 2])

    def test_record_with_only_slim_and_nats_interfaces_has_no_http_url(self):
        record = {
            "name": "Bus only",
            "supportedInterfaces": [
                {
                    "url": "slim://slim:46357/x",
                    "protocolBinding": "slimpatterns",
                    "protocolVersion": "1.0",
                },
                {
                    "url": "nats://nats:4222/x",
                    "protocolBinding": "natspatterns",
                    "protocolVersion": "1.0",
                },
            ],
        }

        with pytest.raises(ValueError, match="url"):
            parse_a2a_agent_record(record)

    def test_parsing_does_not_modify_the_record(self):
        record = json.loads(json.dumps(V03_CARD))

        parse_a2a_agent_record(record)

        assert record == V03_CARD


class TestTaskCallback:
    @staticmethod
    def _status(task_id, state, text=None, metadata=None):
        message = (
            Message(
                message_id=str(uuid4()), role=Role.ROLE_AGENT, parts=[text_part(text)]
            )
            if text
            else None
        )
        status = TaskStatus(state=state)
        if message is not None:
            status.message.CopyFrom(message)
        event = TaskStatusUpdateEvent(task_id=task_id, context_id="c1", status=status)
        if metadata:
            event.metadata.CopyFrom(to_struct(metadata))
        return StreamResponse(status_update=event)

    def test_task_then_status_updates_accumulate_status_text(self):
        callback = GenericTaskUpdateCallback()
        card = AGENT_CARD

        callback.task_callback(
            StreamResponse(
                task=Task(
                    id="t1",
                    context_id="c1",
                    status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
                )
            ),
            card,
        )
        callback.task_callback(
            self._status("t1", TaskState.TASK_STATE_WORKING, "one "), card
        )
        task = callback.task_callback(
            self._status("t1", TaskState.TASK_STATE_COMPLETED, "two"), card
        )

        assert task.status.state == TaskState.TASK_STATE_COMPLETED
        assert parts_text(list(task.status.message.parts)) == "one two"

    def test_later_status_timestamps_are_kept(self):
        callback = GenericTaskUpdateCallback()
        first = TaskStatus(state=TaskState.TASK_STATE_SUBMITTED)
        first.timestamp.FromSeconds(100)
        callback.task_callback(
            StreamResponse(task=Task(id="t4", context_id="c1", status=first)),
            AGENT_CARD,
        )
        update = self._status("t4", TaskState.TASK_STATE_WORKING, "x")
        update.status_update.status.timestamp.FromSeconds(200)

        task = callback.task_callback(update, AGENT_CARD)

        assert task.status.timestamp.seconds == 200

    def test_status_update_without_a_task_creates_one(self):
        callback = GenericTaskUpdateCallback()

        task = callback.task_callback(
            self._status("t2", TaskState.TASK_STATE_WORKING, "hi", {"k": "v"}),
            AGENT_CARD,
        )

        assert task.id == "t2"
        assert task.metadata["k"] == "v"

    def test_artifacts_append_and_merge(self):
        callback = GenericTaskUpdateCallback()

        def update(append, text):
            return StreamResponse(
                artifact_update=TaskArtifactUpdateEvent(
                    task_id="t3",
                    context_id="c1",
                    append=append,
                    artifact=Artifact(
                        artifact_id="a1", name="result", parts=[text_part(text)]
                    ),
                )
            )

        callback.task_callback(update(False, "A"), AGENT_CARD)
        task = callback.task_callback(update(True, "B"), AGENT_CARD)

        assert len(task.artifacts) == 1
        assert parts_text(list(task.artifacts[0].parts)) == "AB"

    def test_message_events_carry_no_task(self):
        callback = GenericTaskUpdateCallback()

        assert (
            callback.task_callback(StreamResponse(message=Message()), AGENT_CARD)
            is None
        )


class TestRemoteAgentConnection:
    @pytest.fixture
    def app(self, monkeypatch):
        """A stand-in for an evaluated agent that answers A2A v1.0 and v0.3.

        The recruiter server itself is v1.0 only; an outside agent the evaluator
        calls can still be a v0.3 server (``enable_v0_3_compat``), so this app
        answers both. The lungo farms are v1.0 only.
        """
        monkeypatch.setattr(executor_module, "RecruiterTeam", FakeTeam)
        handler = DefaultRequestHandler(
            agent_executor=executor_module.RecruiterAgentExecutor(),
            task_store=InMemoryTaskStore(),
            agent_card=AGENT_CARD,
        )
        return Starlette(
            routes=[
                *create_agent_card_routes(AGENT_CARD),
                *create_jsonrpc_routes(handler, rpc_url="/", enable_v0_3_compat=True),
            ]
        )

    @staticmethod
    def _card(protocol_version):
        card = type(AGENT_CARD)()
        card.CopyFrom(AGENT_CARD)
        del card.supported_interfaces[:]
        card.supported_interfaces.append(
            AgentInterface(
                protocol_binding="JSONRPC",
                url="http://recruiter.test/",
                protocol_version=protocol_version,
            )
        )
        return card

    @pytest.mark.parametrize("protocol_version", ["1.0", "0.3"])
    async def test_send_message_returns_the_task_with_the_final_message(
        self, app, protocol_version
    ):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, timeout=30) as http:
            connection = await RemoteAgentConnections.create(
                http, self._card(protocol_version)
            )
            response = await connection.send_message(
                Message(
                    message_id=str(uuid4()),
                    role=Role.ROLE_USER,
                    parts=[text_part("find")],
                )
            )

        assert isinstance(response, Task)
        assert response.status.state == TaskState.TASK_STATE_COMPLETED
        text = A2AEvaluatorAgent._get_text_from_response(response)
        assert "found for: find" in text
        assert json.dumps(FOUND_RECORDS) in text

    async def test_a_failing_server_raises(self):
        def handler(request):
            return httpx.Response(500, text="boom")

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            connection = await RemoteAgentConnections.create(http, self._card("1.0"))
            with pytest.raises(Exception):
                await connection.send_message(
                    Message(message_id="m", role=Role.ROLE_USER, parts=[text_part("x")])
                )


class TestEnsureJsonrpcInterface:
    """The evaluator fetches a live card and must cope with cards as agents publish them."""

    ADDRESS = "http://farm.test:9998"

    @staticmethod
    def _card(*interfaces):
        card = AgentCard(name="Farm")
        card.supported_interfaces.extend(interfaces)
        return card

    def test_lungo_farm_card_is_patched_to_the_evaluated_address(self):
        # The lungo farms publish lowercase "jsonrpc" with a wildcard bind url,
        # next to SLIM and NATS interfaces the recruiter cannot use.
        card = self._card(
            AgentInterface(
                url="slim://slim:46357/lungo/agents/farm",
                protocol_binding="slimpatterns",
                protocol_version="1.0",
            ),
            AgentInterface(
                url="http://0.0.0.0:9998",
                protocol_binding="jsonrpc",
                protocol_version="1.0",
            ),
        )

        ensure_jsonrpc_interface(card, self.ADDRESS)

        assert len(card.supported_interfaces) == 1
        interface = card.supported_interfaces[0]
        assert interface.url == self.ADDRESS
        assert interface.protocol_binding == "JSONRPC"
        assert interface.protocol_version == "1.0"
        ClientFactory(ClientConfig()).create(card)

    def test_lowercase_binding_with_a_dialable_url_is_kept_and_normalized(self):
        card = self._card(
            AgentInterface(
                url="http://farm.internal:9998",
                protocol_binding="jsonrpc",
                protocol_version="1.0",
            )
        )

        ensure_jsonrpc_interface(card, self.ADDRESS)

        interface = card.supported_interfaces[0]
        assert interface.url == "http://farm.internal:9998"
        assert interface.protocol_binding == "JSONRPC"

    def test_a_usable_interface_is_the_only_one_left_so_the_factory_cannot_pick_another(
        self,
    ):
        # ClientFactory prefers an interface declaring 1.0 over the first match,
        # so the undialable 1.0 interface must not survive next to a dialable 0.3.
        card = self._card(
            AgentInterface(
                url="http://0.0.0.0:9998",
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            ),
            AgentInterface(
                url="http://farm.internal:9998",
                protocol_binding="jsonrpc",
                protocol_version="0.3",
            ),
        )

        ensure_jsonrpc_interface(card, self.ADDRESS)

        assert [i.url for i in card.supported_interfaces] == [
            "http://farm.internal:9998"
        ]
        client = ClientFactory(ClientConfig()).create(card)
        assert client._transport.url == "http://farm.internal:9998"

    def test_card_without_any_interface_uses_the_address_as_v03(self):
        card = self._card()

        ensure_jsonrpc_interface(card, self.ADDRESS)

        interface = card.supported_interfaces[0]
        assert (interface.url, interface.protocol_version) == (self.ADDRESS, "0.3")

    def test_empty_url_is_replaced(self):
        card = self._card(
            AgentInterface(url="", protocol_binding="JSONRPC", protocol_version="0.3")
        )

        ensure_jsonrpc_interface(card, self.ADDRESS)

        assert card.supported_interfaces[0].url == self.ADDRESS

    def test_loopback_url_is_replaced_when_the_card_was_fetched_from_elsewhere(self):
        # FARM_AGENT_HOST defaults to localhost: dialed from the recruiter it
        # would reach the recruiter itself, not the farm.
        card = self._card(
            AgentInterface(
                url="http://localhost:9998",
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        )

        ensure_jsonrpc_interface(card, "http://host.docker.internal:9998")

        assert [i.url for i in card.supported_interfaces] == [
            "http://host.docker.internal:9998"
        ]

    @pytest.mark.parametrize("card_url", ["http://localhost:9998", "http://127.0.0.1:9998"])
    def test_loopback_url_is_kept_when_the_card_was_fetched_over_loopback(self, card_url):
        card = self._card(
            AgentInterface(
                url=card_url, protocol_binding="JSONRPC", protocol_version="1.0"
            )
        )

        ensure_jsonrpc_interface(card, "http://localhost:9998")

        assert [i.url for i in card.supported_interfaces] == [card_url]

    def test_jsonrpc_interface_with_a_non_http_url_is_replaced(self):
        card = self._card(
            AgentInterface(
                url="slim://slim:46357/lungo/agents/farm",
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        )

        ensure_jsonrpc_interface(card, self.ADDRESS)

        assert [i.url for i in card.supported_interfaces] == [self.ADDRESS]
        client = ClientFactory(ClientConfig()).create(card)
        assert client._transport.url == self.ADDRESS


class TestEvaluatorEndToEnd:
    """The evaluator resolves a live card, patches it and talks to the agent."""

    @pytest.fixture
    def app(self, monkeypatch):
        monkeypatch.setattr(executor_module, "RecruiterTeam", FakeTeam)
        # Some agents publish their bind address in the card; the recruiter itself
        # no longer does, so a card with a wildcard URL is built here.
        card = AgentCard()
        card.CopyFrom(AGENT_CARD)
        for interface in card.supported_interfaces:
            interface.url = "http://0.0.0.0:8881"
        return build_app(card, executor_module.RecruiterAgentExecutor())

    @staticmethod
    def _evaluator(http):
        from rogue_sdk.types import Scenarios

        return A2AEvaluatorAgent(
            evaluated_agent_address="http://recruiter.test",
            transport=None,
            scenarios=Scenarios(scenarios=[]),
            business_context=None,
            http_client=http,
        )

    async def test_card_with_a_wildcard_url_is_dialed_on_the_evaluated_address(
        self, app
    ):
        # A card that advertises http://0.0.0.0:8881 only works on the host that
        # runs it. The evaluator must use the address it fetched the card from.
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, timeout=30) as http:
            evaluator = self._evaluator(http)

            result = await evaluator._send_message_to_evaluated_agent("ctx-1", "find")

        assert "error" not in result, result
        assert "found for: find" in result["response"]

    async def test_a_failing_agent_returns_an_error_instead_of_raising(self):
        def handler(request):
            return httpx.Response(500, text="boom")

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            evaluator = self._evaluator(http)

            result = await evaluator._send_message_to_evaluated_agent("ctx-2", "find")

        assert result["response"] == ""
        assert result["error"]


class TestEvaluatorResponseText:
    def test_message_text_joins_text_and_data_parts(self):
        message = Message(
            role=Role.ROLE_AGENT,
            parts=[text_part("hello "), data_part({"a": 1})],
        )

        assert A2AEvaluatorAgent._get_text_from_response(message) == 'hello {"a": 1}'

    def test_task_with_artifacts_prefers_artifact_text(self):
        task = Task(
            id="t",
            artifacts=[Artifact(artifact_id="a", name="out", parts=[text_part("x")])],
        )
        task.status.message.parts.append(text_part("status"))

        assert A2AEvaluatorAgent._get_text_from_response(task) == "Artifact: out:\nx\n"

    def test_task_without_artifacts_uses_the_status_message(self):
        task = Task(id="t")
        task.status.message.parts.append(text_part("status"))

        assert A2AEvaluatorAgent._get_text_from_response(task) == "status"

    def test_task_without_any_content_has_no_text(self):
        assert A2AEvaluatorAgent._get_text_from_response(Task(id="t")) is None


def test_data_part_round_trips_nested_values():
    value = {"records": {"cid": {"name": "x", "tags": ["a", "b"], "n": 3}}}

    decoded = part_data(data_part(value))

    assert decoded == value
    assert isinstance(decoded["records"]["cid"]["n"], int)
