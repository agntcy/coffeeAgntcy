# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for common.slim_placeholder_secret.

The app SDK's CardBuilder refuses to start a SLIM interface without a real
shared secret unless allow_placeholder_secret() is called. These tests run the
real CardBuilder.dry_run(), so they also pin that SDK contract.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import config.config
import pytest
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from agntcy_app_sdk.app_sessions import AppSession
from agntcy_app_sdk.semantic.a2a.transport_types import InterfaceTransport
from agntcy_app_sdk.transport.slim.common import PLACEHOLDER_SHARED_SECRET
from common.slim_placeholder_secret import (
    apply_placeholder_secret_policy,
    start_builder,
)

REAL_SECRET = "x" * 40


def _builder():
    card = AgentCard(
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
                url="slim://localhost:46357/test_topic",
            ),
        ],
    )
    return AppSession().add_a2a_card(card, MagicMock()).with_factory(MagicMock())


@pytest.fixture
def allow_placeholder(monkeypatch):
    def _set(value: bool) -> None:
        monkeypatch.setattr(config.config, "SLIM_ALLOW_PLACEHOLDER_SECRET", value)

    return _set


@pytest.mark.parametrize(
    "secret",
    [None, "", PLACEHOLDER_SHARED_SECRET],
    ids=["unset", "empty", "placeholder"],
)
async def test_without_flag_a_missing_secret_stops_the_slim_interface(
    monkeypatch, allow_placeholder, secret
):
    allow_placeholder(False)
    if secret is None:
        monkeypatch.delenv("SLIM_SHARED_SECRET", raising=False)
    else:
        monkeypatch.setenv("SLIM_SHARED_SECRET", secret)

    with pytest.raises(ValueError, match="SLIM shared secret required"):
        await apply_placeholder_secret_policy(_builder()).dry_run()


@pytest.mark.parametrize(
    "secret", [None, PLACEHOLDER_SHARED_SECRET], ids=["unset", "placeholder"]
)
async def test_with_flag_the_placeholder_is_allowed(
    monkeypatch, allow_placeholder, secret
):
    allow_placeholder(True)
    if secret is None:
        monkeypatch.delenv("SLIM_SHARED_SECRET", raising=False)
    else:
        monkeypatch.setenv("SLIM_SHARED_SECRET", secret)

    plan = await apply_placeholder_secret_policy(_builder()).dry_run()

    assert [c["transport"] for c in plan.containers] == ["slimpatterns"]


async def test_start_builder_names_the_corto_settings(monkeypatch, allow_placeholder):
    allow_placeholder(False)
    monkeypatch.delenv("SLIM_SHARED_SECRET", raising=False)

    with pytest.raises(ValueError) as exc:
        await start_builder(
            apply_placeholder_secret_policy(_builder()), keep_alive=False
        )

    message = str(exc.value)
    assert message.startswith("SLIM shared secret required")
    assert "SLIM_ALLOW_PLACEHOLDER_SECRET=true" in message
    assert ".allow_placeholder_secret()" not in message
    assert isinstance(exc.value.__cause__, ValueError)


async def test_start_builder_leaves_other_errors_alone():
    builder = MagicMock()
    builder.start = AsyncMock(side_effect=ValueError("other"))

    with pytest.raises(ValueError, match="^other$"):
        await start_builder(builder)


@pytest.mark.parametrize("flag", [False, True])
async def test_a_real_secret_starts_whatever_the_flag(
    monkeypatch, allow_placeholder, flag
):
    allow_placeholder(flag)
    monkeypatch.setenv("SLIM_SHARED_SECRET", REAL_SECRET)

    plan = await apply_placeholder_secret_policy(_builder()).dry_run()

    assert [c["transport"] for c in plan.containers] == ["slimpatterns"]
