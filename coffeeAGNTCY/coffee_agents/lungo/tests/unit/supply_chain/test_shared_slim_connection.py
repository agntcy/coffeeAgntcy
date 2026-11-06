# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Every SLIM transport in the Buyer's process shares one connection.

A health probe must not cut it. The Buyer's ``/v1/health`` and the members'
``/v1/health`` each open a client and close it. With agntcy-app-sdk 0.6.0 that
close disconnected the shared connection and left its id cached, so the next
caller (a broadcast client, the next probe) was handed a dead id and failed with
"connection not found". agntcy-app-sdk 0.6.1 counts the transports on the
connection and only the last ``close()`` disconnects.

A connection that really dies must be replaced. Closing the broadcast client that
hit the failure only gives back its share, so while another transport holds the
connection the SDK would hand the same dead one to the next client unless the
failure is reported.

These tests run the real routes, ``SlimGroupTransport`` and ``SLIMTransport``
against a fake SLIM service that rejects a dead connection the way the real one
does. The probe tests fail on 0.6.0 and guard against pinning it again.
"""

from __future__ import annotations

import itertools
import secrets
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from a2a.types import AgentCard
from agntcy_app_sdk.transport.slim import common
from agntcy_app_sdk.transport.slim.transport import SLIMTransport

from agents.supervisors.supply_chain import main as buyer_main
from agents.supervisors.supply_chain.transport import SlimGroupTransport, TransportError
from agents.supply_chain.common import member_server
from agents.supply_chain.common.envelope import Envelope
from agents.supply_chain.logistics.card import AGENT_CARD as LOGISTICS_CARD
from agents.supply_chain.supplier.card import AGENT_CARDS as SUPPLIER_CARDS

_ENDPOINT = "http://slim.example:46357"
# Generated per run: the SDK only needs some secret, and none is kept in the repo.
_SECRET = secrets.token_hex(24)


class FakeSlimService:
    """Stands in for ``slim_bindings.Service``: it tracks which connections are live."""

    def __init__(self) -> None:
        self._ids = itertools.count(100)
        self.live: set[int] = set()
        self.disconnected: list[int] = []
        self.connect_async = AsyncMock(side_effect=self._connect)

    async def _connect(self, _config) -> int:
        connection_id = next(self._ids)
        self.live.add(connection_id)
        return connection_id

    def create_app(self, *_args) -> MagicMock:
        app = MagicMock()
        app.subscribe_async = AsyncMock()

        async def set_route(_name, connection_id: int) -> None:
            # What the real dataplane answers for a connection that is gone.
            if connection_id not in self.live:
                raise RuntimeError(f"connection not found: {connection_id}")

        app.set_route_async = AsyncMock(side_effect=set_route)
        return app

    def disconnect(self, connection_id: int) -> None:
        self.live.discard(connection_id)
        self.disconnected.append(connection_id)


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> FakeSlimService:
    """A fake SLIM service behind the SDK's process-wide connection cache."""
    service = FakeSlimService()
    for name, value in (
        ("global_slim", None),
        ("global_slim_service", None),
        ("global_connection_id", None),
        ("global_slim_insecure", None),
        ("global_slim_endpoint", None),
        ("global_slim_auth", None),
        # Only agntcy-app-sdk 0.6.1 and later count users, so the test must still
        # load on 0.6.0 and fail on the behaviour, not on a missing attribute.
        ("global_slim_users", 0),
        ("_retired_connection_users", {}),
    ):
        monkeypatch.setattr(common, name, value, raising=False)
    monkeypatch.setattr(common, "get_or_init_slim_service", lambda: service)
    monkeypatch.setattr(common, "shared_secret_identity", lambda **_kw: (None, None))
    monkeypatch.setattr(common, "new_client_config", lambda *_a, **_kw: "config")
    return service


def _transport(name: str) -> SLIMTransport:
    return SLIMTransport(
        routable_name=f"lungo/agents/{name}",
        endpoint=_ENDPOINT,
        shared_secret_identity=_SECRET,
    )


class ProbeClient:
    """What the probes close: the SDK client closes its transport, and so does this."""

    def __init__(self, transport: SLIMTransport) -> None:
        self._transport = transport

    async def close(self) -> None:
        await self._transport.close()


class ProbeClientFactory:
    """Builds a client on a new SLIM transport, as ``A2AClientFactory.create`` does."""

    def __init__(self, *_args, **_kwargs) -> None:
        self.created = 0

    async def create(self, _card, **_kwargs) -> ProbeClient:
        self.created += 1
        transport = _transport(f"probe-{self.created}")
        await transport.setup()
        return ProbeClient(transport)


async def _route_through(transport: SLIMTransport) -> None:
    """The first thing a transport does to talk to a peer: set a route."""
    assert transport._slim_app is not None
    await transport._slim_app.set_route_async(
        transport.build_name("peer"), transport._slim_connection_id
    )


async def _long_lived_user() -> SLIMTransport:
    """A transport that stays open, like the Buyer's cached broadcast client."""
    keeper = _transport("keeper")
    await keeper.setup()
    return keeper


@pytest.mark.parametrize("probes", [1, 2])
async def test_buyer_health_probe_leaves_the_connection_to_the_others(
    service: FakeSlimService, monkeypatch: pytest.MonkeyPatch, probes: int
) -> None:
    keeper = await _long_lived_user()
    monkeypatch.setattr(buyer_main, "a2a_client_factory", ProbeClientFactory())
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(supply_chain_runner=object()))
    )

    for _ in range(probes):
        assert await buyer_main.connectivity_health(request) == {"status": "alive"}

    assert service.disconnected == [], "a probe closed a connection others still use"
    await _route_through(keeper)

    await keeper.close()
    assert len(service.disconnected) == 1, "the last close disconnects, once"


@pytest.mark.parametrize("probes", [1, 2])
async def test_member_health_probe_leaves_the_connection_to_the_others(
    service: FakeSlimService, monkeypatch: pytest.MonkeyPatch, probes: int
) -> None:
    keeper = await _long_lived_user()
    monkeypatch.setattr(member_server, "A2AClientFactory", ProbeClientFactory)
    probe = member_server.make_liveness_probe("lungo/agents/member", AgentCard())

    for _ in range(probes):
        response = await probe(request=None)
        assert response.status_code == 200, response.body

    assert service.disconnected == [], "a probe closed a connection others still use"
    await _route_through(keeper)

    await keeper.close()
    assert len(service.disconnected) == 1, "the last close disconnects, once"


async def test_a_call_after_a_probe_finds_a_live_connection(
    service: FakeSlimService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The order that broke the weather test: probe first, a real call after it."""
    monkeypatch.setattr(buyer_main, "a2a_client_factory", ProbeClientFactory())
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(supply_chain_runner=object()))
    )
    assert await buyer_main.connectivity_health(request) == {"status": "alive"}

    later = _transport("later")
    await later.setup()

    await _route_through(later)
    await later.close()


class BroadcastClient:
    """Stands in for the SDK's experimental client: a SLIM transport and a broadcast."""

    def __init__(self, transport: SLIMTransport) -> None:
        self.transport = transport

    async def broadcast_message(self, *_args, **_kwargs) -> list:
        await _route_through(self.transport)
        return []

    async def close(self) -> None:
        await self.transport.close()


class BroadcastClientFactory:
    def __init__(self) -> None:
        self.created: list[BroadcastClient] = []

    async def create(self, _card, interceptors=()) -> BroadcastClient:
        transport = _transport(f"buyer-{len(self.created)}")
        await transport.setup()
        client = BroadcastClient(transport)
        self.created.append(client)
        return client


def _step(seq: int) -> Envelope:
    return Envelope(
        run_id="r1",
        seq=seq,
        sender="buyer",
        to=("supplier_a",),
        kind="negotiation",
        body="offer",
    )


async def test_a_connection_that_died_is_replaced_for_the_next_broadcast(
    service: FakeSlimService,
) -> None:
    """The server drops the connection while another transport still holds it.

    The failed client's close gives back only its own share, so without the
    report the next client is built on the same dead connection and fails again.
    """
    keeper = await _long_lived_user()
    cards = {"logistics": LOGISTICS_CARD, **SUPPLIER_CARDS}
    factory = BroadcastClientFactory()
    transport = SlimGroupTransport(factory, cards)

    assert await transport.broadcast(_step(1), ["supplier_a"], timeout=5) == []
    service.live.clear()  # a SLIM server restart: every connection is gone

    with pytest.raises(TransportError, match="connection not found"):
        await transport.broadcast(_step(2), ["supplier_a"], timeout=5)
    assert await transport.broadcast(_step(3), ["supplier_a"], timeout=5) == []

    first, replacement = factory.created
    assert replacement.transport._slim_connection_id != (
        first.transport._slim_connection_id
    )
    assert keeper._slim_connection_id == first.transport._slim_connection_id, (
        "the transport that was already on the old connection keeps it"
    )
