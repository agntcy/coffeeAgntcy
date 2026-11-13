# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.supervisors.recruiter.recruiter_service_card."""

import importlib
import sys

import pytest

MODULE = "agents.supervisors.recruiter.recruiter_service_card"
DEFAULT_URL = "http://localhost:8881"


@pytest.fixture()
def load_card(monkeypatch):
    """Import the card module fresh under the current env.

    Other tests in this package purge ``agents.supervisors.recruiter*`` from
    ``sys.modules``, so the module is dropped and imported again here instead of
    being imported at the top of the file and reloaded.
    """

    def _load():
        sys.modules.pop(MODULE, None)
        return importlib.import_module(MODULE)

    yield _load

    monkeypatch.undo()
    sys.modules.pop(MODULE, None)


def test_unset_recruiter_agent_url_uses_the_default(monkeypatch, load_card):
    monkeypatch.delenv("RECRUITER_AGENT_URL", raising=False)

    card_module = load_card()

    assert card_module.RECRUITER_AGENT_URL == DEFAULT_URL
    assert card_module.RECRUITER_AGENT_CARD.supported_interfaces[0].url == DEFAULT_URL


def test_empty_recruiter_agent_url_falls_back_to_the_default(monkeypatch, load_card):
    # The recruiter-supervisor chart renders RECRUITER_AGENT_URL="" when
    # recruiterAgentUrl is unset.
    monkeypatch.setenv("RECRUITER_AGENT_URL", "")

    card_module = load_card()

    assert card_module.RECRUITER_AGENT_URL == DEFAULT_URL
    assert card_module.RECRUITER_AGENT_CARD.supported_interfaces[0].url == DEFAULT_URL


def test_configured_recruiter_agent_url_is_used(monkeypatch, load_card):
    monkeypatch.setenv("RECRUITER_AGENT_URL", "http://recruiter:8881")

    card_module = load_card()

    assert card_module.RECRUITER_AGENT_URL == "http://recruiter:8881"
    assert (
        card_module.RECRUITER_AGENT_CARD.supported_interfaces[0].url
        == "http://recruiter:8881"
    )
