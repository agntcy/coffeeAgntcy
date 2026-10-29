# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import pytest


@pytest.fixture(autouse=True)
def _l9_switch_on_unless_a_test_says_otherwise(monkeypatch):
    """Run the unit tests with L9 on, whatever a developer's ``.env`` says.

    ``load_dotenv`` puts a local ``SUPPLY_CHAIN_L9_ENABLED`` into the
    environment, and the deployment default is off, so most tests that
    exercise ACCORD or CONCORD would otherwise depend on a local file. A test
    for the switch passes its own mapping to ``l9_enabled`` or sets the
    variable itself.
    """
    monkeypatch.setenv("SUPPLY_CHAIN_L9_ENABLED", "true")
