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


def _save_modules(prefixes):
  """Return a dict of module name -> module for all modules matching prefixes."""
  return {
    m: sys.modules[m]
    for m in list(sys.modules)
    if any(m == p or m.startswith(p + ".") for p in prefixes)
  }


def _restore_modules(saved):
  """Put saved modules back into sys.modules so other tests see the same state as before."""
  for name, mod in saved.items():
    sys.modules[name] = mod


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
  import config.config as config_mod
  saved_ensure = getattr(config_mod, "ENSURE_STREAMING_LLM", False)
  saved_llm_model = getattr(config_mod, "LLM_MODEL", "")

  prefix = import_module.rsplit(".", 1)[0]
  prefixes = [prefix, "common"]
  saved_modules = _save_modules(prefixes)
  try:
    with patch("litellm.get_model_info", return_value={"supports_native_streaming": False}) as mock_get_model_info:
      _purge_modules(prefixes)
      monkeypatch.setattr(config_mod, "ENSURE_STREAMING_LLM", True)
      monkeypatch.setattr(config_mod, "LLM_MODEL", "openai/gpt-4o-mini")
      try:
        importlib.import_module(import_module)
      except Exception as e:
        assert type(e).__name__ == "StreamingNotSupportedError", f"Expected StreamingNotSupportedError, got {type(e)}"
        assert e.agent_name == expected_agent_name
        mock_get_model_info.assert_called_once_with(model="openai/gpt-4o-mini")
        return
    pytest.fail("Expected StreamingNotSupportedError")
  finally:
    monkeypatch.setattr(config_mod, "ENSURE_STREAMING_LLM", saved_ensure)
    monkeypatch.setattr(config_mod, "LLM_MODEL", saved_llm_model)
    _purge_modules(prefixes)
    _restore_modules(saved_modules)

