# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""build_a2a_client_config hands the SLIM shared secret to the app SDK unchanged.

The SDK resolves it when the transport connects (argument, then
SLIM_SHARED_SECRET, then its public placeholder), so an unset or empty variable
must not make the config builder raise.
"""

import pytest
from common import a2a_transport_config
from common.a2a_transport_config import build_a2a_client_config


@pytest.fixture(autouse=True)
def _no_timeout_patch(monkeypatch):
    # The timeout patch edits the SLIM transport class, which is irrelevant here.
    monkeypatch.setattr(
        a2a_transport_config, "apply_slim_request_timeout", lambda _: None
    )


def _build(include_nats: bool = False):
    return build_a2a_client_config(
        namespace="lungo",
        group="agents",
        agent_name="test_supervisor",
        include_nats=include_nats,
    )


def test_secret_from_env_is_passed_through(monkeypatch):
    monkeypatch.setenv("SLIM_SHARED_SECRET", "x" * 40)

    assert _build().slim_config.shared_secret_identity == "x" * 40


@pytest.mark.parametrize("value", [None, ""])
def test_unset_or_empty_secret_does_not_raise_and_is_left_to_the_sdk(
    monkeypatch, value
):
    if value is None:
        monkeypatch.delenv("SLIM_SHARED_SECRET", raising=False)
    else:
        monkeypatch.setenv("SLIM_SHARED_SECRET", value)

    assert _build().slim_config.shared_secret_identity is None


def test_slim_name_is_namespace_group_agent(monkeypatch):
    monkeypatch.setenv("SLIM_SHARED_SECRET", "x" * 40)

    assert _build().slim_config.name == "lungo/agents/test_supervisor"
