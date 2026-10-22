# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the farm servers' fault-tolerant multi-transport serving.

A startup failure on the preferred transport (the first entry of the card's
``supported_interfaces``) must be fatal, while a failure on any other
advertised transport must be logged and skipped so a single unavailable broker
(e.g. NATS) cannot take the whole agent down.

The three coffee-farm servers (Brazil, Colombia, Vietnam) share the same
``serve_all_a2a_interfaces`` implementation, so every case is parametrized
across all three modules.
"""

from __future__ import annotations

import importlib

import pytest
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from agntcy_app_sdk import A2AServerConfig
from agntcy_app_sdk.semantic.a2a.transport_types import (
    InterfaceTransport,
    normalize_transport,
)

FARM_SERVER_MODULES = [
    "agents.farms.brazil.farm_server",
    "agents.farms.colombia.farm_server",
    "agents.farms.vietnam.farm_server",
]


def _make_card() -> AgentCard:
    """Card in today's farm order: SLIM (preferred), NATS, JSON-RPC."""
    return AgentCard(
        name="Test Farm",
        description="test card",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[AgentSkill(id="s", name="s", description="d", tags=["t"])],
        supported_interfaces=[
            AgentInterface(
                protocol_binding=InterfaceTransport.SLIM_PATTERNS,
                url="slim://localhost:46357/topic",
            ),
            AgentInterface(
                protocol_binding=InterfaceTransport.NATS_PATTERNS,
                url="nats://localhost:4222/topic",
            ),
            AgentInterface(
                protocol_binding=InterfaceTransport.JSONRPC,
                url="http://0.0.0.0:9999/",
            ),
        ],
    )


class _FakeBuilder:
    def __init__(self, session: "_FakeSession", card: AgentCard):
        self._session = session
        self._card = card
        self._skips: set[str] = set()

    def with_factory(self, _factory):
        return self

    def allow_placeholder_secret(self):
        self._session.placeholder_allowed = True
        return self

    def skip(self, transport_type: str):
        self._skips.add(normalize_transport(transport_type))
        return self

    def override(self, transport_type: str, target):
        self._session.overrides[normalize_transport(transport_type)] = target
        return self

    async def start(self, *, keep_alive: bool = False):
        advertised = {
            normalize_transport(i.protocol_binding)
            for i in self._card.supported_interfaces
        }
        served = advertised - self._skips
        assert len(served) == 1, f"expected exactly one served transport, got {served}"
        transport = next(iter(served))
        self._session.served_transport = transport
        if transport in self._session._fail_transports:
            raise RuntimeError(f"{transport} broker unavailable")


class _FakeSession:
    def __init__(self, fail_transports: set[str]):
        self._fail_transports = fail_transports
        self.served_transport: str | None = None
        self.start_all_called_with: bool | None = None
        self.overrides: dict = {}
        self.placeholder_allowed = False

    def add_a2a_card(self, card: AgentCard, _handler):
        return _FakeBuilder(self, card)

    async def start_all_sessions(self, keep_alive: bool = False):
        self.start_all_called_with = keep_alive


class _FakeFactory:
    def __init__(self, fail_transports: set[str]):
        self._fail_transports = fail_transports
        self.sessions: list[_FakeSession] = []

    def create_app_session(self) -> _FakeSession:
        session = _FakeSession(self._fail_transports)
        self.sessions.append(session)
        return session


@pytest.fixture
def patch_factory(monkeypatch):
    def _install(module_name: str, fail_transports: set[str]) -> _FakeFactory:
        module = importlib.import_module(module_name)
        fake = _FakeFactory(set(fail_transports))
        monkeypatch.setattr(module, "factory", fake)
        return module, fake

    return _install


@pytest.mark.parametrize("module_name", FARM_SERVER_MODULES)
async def test_non_preferred_transport_failure_is_tolerated(patch_factory, module_name):
    # NATS is down; SLIM (preferred) and jsonrpc are healthy.
    module, fake = patch_factory(module_name, {"natspatterns"})
    card = _make_card()

    # Must NOT raise even though the NATS interface fails to start.
    await module.serve_all_a2a_interfaces(object(), card)

    # One session created per advertised interface, in card order.
    assert [s.served_transport for s in fake.sessions] == [
        "slimpatterns",
        "natspatterns",
        "jsonrpc",
    ]

    # The keep-alive loop is entered on the first healthy session (SLIM),
    # never on the failed NATS session.
    slim_session, nats_session, jsonrpc_session = fake.sessions
    assert slim_session.start_all_called_with is True
    assert nats_session.start_all_called_with is None
    assert jsonrpc_session.start_all_called_with is None


@pytest.mark.parametrize("module_name", FARM_SERVER_MODULES)
async def test_preferred_transport_failure_is_fatal(patch_factory, module_name):
    # SLIM is the preferred transport and it is down -> must crash.
    module, _fake = patch_factory(module_name, {"slimpatterns"})
    card = _make_card()

    with pytest.raises(RuntimeError, match="broker unavailable"):
        await module.serve_all_a2a_interfaces(object(), card)


@pytest.mark.parametrize("module_name", FARM_SERVER_MODULES)
async def test_all_transports_failing_raises(patch_factory, module_name):
    # The first interface is always the preferred one, so when every transport
    # is down the preferred failure aborts startup before the others are tried.
    module, fake = patch_factory(
        module_name, {"slimpatterns", "natspatterns", "jsonrpc"}
    )
    card = _make_card()

    with pytest.raises(RuntimeError, match="broker unavailable"):
        await module.serve_all_a2a_interfaces(object(), card)
    assert [s.served_transport for s in fake.sessions] == ["slimpatterns"]


@pytest.mark.parametrize("module_name", FARM_SERVER_MODULES)
async def test_jsonrpc_interface_accepts_a2a_v03_on_a_card_copy(
    patch_factory, module_name
):
    # The HTTP JSON-RPC interface is served through an override that enables
    # A2A v0.3 compatibility (message/send, message/stream) for v0.3 callers.
    module, fake = patch_factory(module_name, set())
    card = _make_card()
    handler = object()

    await module.serve_all_a2a_interfaces(handler, card)

    slim_session, nats_session, jsonrpc_session = fake.sessions
    assert slim_session.overrides == {}
    assert nats_session.overrides == {}
    override = jsonrpc_session.overrides["jsonrpc"]
    assert isinstance(override, A2AServerConfig)
    assert override.enable_v0_3_compat is True
    assert override.request_handler is handler
    # A copy: with identity auth on, the SDK edits the card it serves.
    assert override.agent_card == card
    assert override.agent_card is not card


@pytest.mark.parametrize("module_name", FARM_SERVER_MODULES)
@pytest.mark.parametrize("flag", [False, True])
async def test_placeholder_secret_follows_the_flag(
    patch_factory, monkeypatch, module_name, flag
):
    import config.config

    monkeypatch.setattr(config.config, "SLIM_ALLOW_PLACEHOLDER_SECRET", flag)
    module, fake = patch_factory(module_name, set())

    await module.serve_all_a2a_interfaces(object(), _make_card())

    assert [s.placeholder_allowed for s in fake.sessions] == [flag, flag, flag]
