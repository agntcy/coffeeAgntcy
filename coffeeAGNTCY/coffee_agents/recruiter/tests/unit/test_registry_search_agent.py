# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the registry search agent's MCP toolset wiring (no Docker, no LLM)."""

import pytest

from agent_recruiter.agent_registries import registry_search_agent as rsa


def test_discovery_toolset_launches_dir_mcp_without_subcommand(monkeypatch):
    # `dirctl mcp serve` was removed from dirctl; the standalone dir-mcp binary
    # is the stdio MCP server and takes no arguments.
    monkeypatch.setattr(rsa.shutil, "which", lambda name: f"/usr/local/bin/{name}")

    toolset = rsa.create_discovery_mcp_toolset()

    params = toolset._connection_params.server_params
    assert params.command == "/usr/local/bin/dir-mcp"
    assert not params.args


def test_dir_mcp_path_raises_when_binary_missing(monkeypatch):
    monkeypatch.setattr(rsa.shutil, "which", lambda name: None)

    with pytest.raises(RuntimeError, match="dir-mcp binary not found"):
        rsa._dir_mcp_path()
