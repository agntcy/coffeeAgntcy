# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the farm agent card.

a2a-sdk 1.2 logs an "AgentCard is not spec-compliant" warning for every
interface that leaves ``protocol_version`` empty, so each one must declare it.
"""

from agntcy_app_sdk.semantic.a2a.transport_types import InterfaceTransport
from config.config import FARM_AGENT_PORT
from farm.card import AGENT_CARD


def test_farm_card_interfaces_declare_protocol_version():
    assert AGENT_CARD.supported_interfaces
    assert all(i.protocol_version for i in AGENT_CARD.supported_interfaces)


def test_farm_card_http_interface_holds_the_bind_address():
    """The SDK binds the HTTP server to this url, so it must stay a wildcard.

    A host name here fails to bind in Kubernetes, where the Service name
    resolves to the ClusterIP. Clients get a copy with the public host (see
    ``common.card_public_url``).
    """
    [http] = [
        i
        for i in AGENT_CARD.supported_interfaces
        if i.protocol_binding == InterfaceTransport.JSONRPC
    ]
    assert http.url == f"http://0.0.0.0:{FARM_AGENT_PORT}/"
