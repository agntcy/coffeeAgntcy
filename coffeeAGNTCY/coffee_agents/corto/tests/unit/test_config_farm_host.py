# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""FARM_AGENT_HOST is the host clients dial; an empty value means localhost."""

import importlib

import pytest


def _reload_registered_config():
    # Resolve the module at call time, not import time: the integration
    # supervisor_client fixture drops config.config from sys.modules, and
    # importlib.reload() rejects a module that is no longer registered there.
    return importlib.reload(importlib.import_module("config.config"))


@pytest.fixture
def reload_config(monkeypatch):
    def _reload(value):
        if value is None:
            monkeypatch.delenv("FARM_AGENT_HOST", raising=False)
        else:
            monkeypatch.setenv("FARM_AGENT_HOST", value)
        return _reload_registered_config()

    yield _reload
    monkeypatch.delenv("FARM_AGENT_HOST", raising=False)
    _reload_registered_config()


@pytest.mark.parametrize(
    "value, expected",
    [(None, "localhost"), ("", "localhost"), ("corto-farm", "corto-farm")],
)
def test_farm_agent_host(reload_config, value, expected):
    assert reload_config(value).FARM_AGENT_HOST == expected
