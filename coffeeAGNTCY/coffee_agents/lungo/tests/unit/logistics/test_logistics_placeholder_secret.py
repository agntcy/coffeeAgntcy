# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""The logistics servers apply the SLIM placeholder-secret policy before start."""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import config.config
import pytest

LOGISTICS_SERVER_MODULES = [
    "agents.logistics.accountant.server",
    "agents.logistics.farm.server",
    "agents.logistics.helpdesk.server",
    "agents.logistics.shipper.server",
]


@pytest.mark.parametrize("module_name", LOGISTICS_SERVER_MODULES)
@pytest.mark.parametrize("flag", [False, True])
async def test_logistics_server_applies_placeholder_policy(
    monkeypatch, module_name, flag
):
    monkeypatch.setattr(config.config, "SLIM_ALLOW_PLACEHOLDER_SECRET", flag)
    module = importlib.import_module(module_name)
    builder = MagicMock()
    builder.allow_placeholder_secret.return_value = builder
    builder.start = AsyncMock()
    session = MagicMock()
    session.add_a2a_card.return_value = builder
    monkeypatch.setattr(
        module, "factory", SimpleNamespace(create_app_session=lambda: session)
    )

    await module.serve_all_a2a_interfaces(MagicMock(), module.AGENT_CARD)

    assert builder.allow_placeholder_secret.called == flag
    builder.start.assert_awaited_once_with(keep_alive=False)
