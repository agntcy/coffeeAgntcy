# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Integration-style: with ENSURE_STREAMING_LLM=true, supervisor startup fails when configured LLM does not support streaming."""
import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_root = str(Path(__file__).resolve().parents[3])


def _ensure_root_on_path():
  try:
    sys.path.remove(_root)
  except ValueError:
    pass
  sys.path.insert(0, _root)


_ensure_root_on_path()


def _purge_modules(prefixes):
  to_delete = [
    m
    for m in list(sys.modules)
    if any(m == p or m.startswith(p + ".") for p in prefixes)
  ]
  for m in to_delete:
    sys.modules.pop(m, None)


@pytest.mark.parametrize(
  "import_module,expected_agent_name",
  [
    ("agents.supervisors.auction.main", "auction_supervisor"),
    ("agents.supervisors.logistics.main", "logistics_supervisor"),
    ("agents.supervisors.recruiter.agent", "recruiter_supervisor"),
  ],
  ids=["auction", "logistics", "recruiter"],
)
def test_supervisor_raises_when_llm_does_not_support_streaming(monkeypatch, import_module, expected_agent_name):
  """With ENSURE_STREAMING_LLM=true, supervisor startup fails when get_model_info says no streaming."""
  _ensure_root_on_path()
  monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
  monkeypatch.setenv("ENSURE_STREAMING_LLM", "true")
  with patch("litellm.get_model_info", return_value={"supports_native_streaming": False}):
    prefix = import_module.rsplit(".", 1)[0]
    _purge_modules([prefix, "config.config", "common"])
    try:
      importlib.import_module(import_module)
    except Exception as e:
      assert type(e).__name__ == "StreamingNotSupportedError", f"Expected StreamingNotSupportedError, got {type(e)}"
      assert e.agent_name == expected_agent_name
      return
  pytest.fail("Expected StreamingNotSupportedError")

