# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Member HTTP server: a failure ends the agent instead of exiting cleanly."""

import pytest

from agents.supply_chain.common import member_server


async def test_http_server_failure_propagates(monkeypatch):
    class Boom:
        def __init__(self, config):
            pass

        async def serve(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(member_server, "Server", Boom)
    monkeypatch.setattr(member_server, "build_http_app", lambda server, probe: object())
    with pytest.raises(RuntimeError, match="boom"):
        await member_server.run_http_server(None, None, 0)
