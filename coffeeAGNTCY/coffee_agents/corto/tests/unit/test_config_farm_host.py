# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""FARM_AGENT_HOST is the host clients dial; an empty value means localhost."""

import importlib

import pytest

import config.config as config_module


@pytest.fixture
def reload_config(monkeypatch):
    def _reload(value):
        if value is None:
            monkeypatch.delenv("FARM_AGENT_HOST", raising=False)
        else:
            monkeypatch.setenv("FARM_AGENT_HOST", value)
        return importlib.reload(config_module)

    yield _reload
    monkeypatch.delenv("FARM_AGENT_HOST", raising=False)
    importlib.reload(config_module)


@pytest.mark.parametrize(
    "value, expected",
    [(None, "localhost"), ("", "localhost"), ("corto-farm", "corto-farm")],
)
def test_farm_agent_host(reload_config, value, expected):
    assert reload_config(value).FARM_AGENT_HOST == expected
