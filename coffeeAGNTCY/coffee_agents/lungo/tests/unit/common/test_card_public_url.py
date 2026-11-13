# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the public HTTP host advertised by a farm card copy."""

import logging

import pytest
from a2a.types import AgentCard, AgentInterface
from agntcy_app_sdk.semantic.a2a.transport_types import InterfaceTransport

import common.card_public_url as module
from common.card_public_url import with_public_http_host


def _card(http_url: str) -> AgentCard:
    return AgentCard(
        name="Farm",
        supported_interfaces=[
            AgentInterface(
                protocol_binding=InterfaceTransport.SLIM_PATTERNS,
                url="slim://0.0.0.0:46357/topic",
                protocol_version="1.0",
            ),
            AgentInterface(
                protocol_binding=InterfaceTransport.JSONRPC,
                url=http_url,
                protocol_version="1.0",
            ),
        ],
    )


def _urls(card: AgentCard) -> dict[str, str]:
    return {i.protocol_binding: i.url for i in card.supported_interfaces}


@pytest.mark.parametrize(
    "bind_url, expected",
    [
        ("http://0.0.0.0:9999", "http://farm-server:9999"),
        ("http://0.0.0.0:9999/", "http://farm-server:9999/"),
        ("http://0.0.0.0:9999/a?x=1", "http://farm-server:9999/a?x=1"),
        ("http://0.0.0.0", "http://farm-server"),
        ("http://[::]:9999/", "http://farm-server:9999/"),
    ],
)
def test_wildcard_host_is_replaced_keeping_port_and_path(bind_url, expected):
    served = with_public_http_host(_card(bind_url), "farm-server")

    assert _urls(served)[InterfaceTransport.JSONRPC] == expected


def test_input_card_and_non_http_interfaces_are_left_alone():
    card = _card("http://0.0.0.0:9999")

    served = with_public_http_host(card, "farm-server")

    assert served is not card
    assert _urls(card)[InterfaceTransport.JSONRPC] == "http://0.0.0.0:9999"
    assert (
        _urls(served)[InterfaceTransport.SLIM_PATTERNS] == "slim://0.0.0.0:46357/topic"
    )


def test_an_already_named_host_is_kept():
    served = with_public_http_host(_card("http://brazil-farm:9999"), "other")

    assert _urls(served)[InterfaceTransport.JSONRPC] == "http://brazil-farm:9999"


@pytest.mark.parametrize("host", ["", "0.0.0.0", "::"])
def test_a_wildcard_public_host_is_rejected(host):
    with pytest.raises(ValueError, match="not an address clients can dial"):
        with_public_http_host(_card("http://0.0.0.0:9999"), host)


@pytest.mark.parametrize("in_container", [True, False])
def test_loopback_is_flagged_only_inside_a_container(monkeypatch, caplog, in_container):
    monkeypatch.setattr(module, "_in_container", lambda: in_container)

    with caplog.at_level(logging.WARNING, logger=module.logger.name):
        with_public_http_host(_card("http://0.0.0.0:9999"), "localhost")

    assert bool(caplog.records) is in_container
