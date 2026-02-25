# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for common.streaming_capability. No app-sdk; asserts on return values and exception type/attributes only.
require_streaming_capability tests that exercise the check use ENSURE_STREAMING_LLM=true."""
import importlib.util
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[3]
_cap_path = _root / "common" / "streaming_capability.py"
_STREAMING_MODULE = "_streaming_capability_under_test"
_spec = importlib.util.spec_from_file_location(_STREAMING_MODULE, _cap_path)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_STREAMING_MODULE] = _mod
_spec.loader.exec_module(_mod)

_TEST_MODEL = "openai/gpt-4o-mini"
StreamingNotSupportedError = _mod.StreamingNotSupportedError
get_llm_streaming_capability = _mod.get_llm_streaming_capability
require_streaming_capability = _mod.require_streaming_capability

from unittest.mock import patch

import pytest


class TestGetLlmStreamingCapability:
  def test_returns_true_when_supports_native_streaming_true(self):
    with patch(f"{_STREAMING_MODULE}.litellm.get_model_info", return_value={"supports_native_streaming": True}):
      assert get_llm_streaming_capability(_TEST_MODEL) is True

  def test_returns_false_when_supports_native_streaming_false(self):
    with patch(f"{_STREAMING_MODULE}.litellm.get_model_info", return_value={"supports_native_streaming": False}):
      assert get_llm_streaming_capability(_TEST_MODEL) is False

  def test_returns_false_when_key_missing(self):
    with patch(f"{_STREAMING_MODULE}.litellm.get_model_info", return_value={}):
      assert get_llm_streaming_capability(_TEST_MODEL) is False

  def test_returns_false_when_key_none(self):
    with patch(f"{_STREAMING_MODULE}.litellm.get_model_info", return_value={"supports_native_streaming": None}):
      assert get_llm_streaming_capability(_TEST_MODEL) is False

  def test_returns_false_on_exception(self):
    with patch(f"{_STREAMING_MODULE}.litellm.get_model_info", side_effect=Exception("unknown model")):
      assert get_llm_streaming_capability(_TEST_MODEL) is False


class TestRequireStreamingCapability:
  def test_early_return_when_flag_disabled(self):
    """When ENSURE_STREAMING_LLM is not true, require_streaming_capability returns without raising and does not call get_model_info."""
    with patch(f"{_STREAMING_MODULE}.ENSURE_STREAMING_LLM", False):
      with patch(f"{_STREAMING_MODULE}.litellm.get_model_info") as mock_get_model_info:
        require_streaming_capability("test_agent", _TEST_MODEL)
        mock_get_model_info.assert_not_called()

  def test_does_not_raise_when_capable(self):
    with patch(f"{_STREAMING_MODULE}.ENSURE_STREAMING_LLM", True):
      with patch(f"{_STREAMING_MODULE}.litellm.get_model_info", return_value={"supports_native_streaming": True}):
        require_streaming_capability("test_agent", _TEST_MODEL)

  def test_raises_streaming_not_supported_error_when_not_capable(self):
    with patch(f"{_STREAMING_MODULE}.ENSURE_STREAMING_LLM", True):
      with patch(f"{_STREAMING_MODULE}.litellm.get_model_info", return_value={"supports_native_streaming": False}):
        with pytest.raises(StreamingNotSupportedError) as exc_info:
          require_streaming_capability("test_agent", _TEST_MODEL)
        assert exc_info.value.agent_name == "test_agent"
        assert exc_info.value.model == _TEST_MODEL
        assert len(exc_info.value.message) > 0

  def test_raises_when_get_model_info_raises(self):
    with patch(f"{_STREAMING_MODULE}.ENSURE_STREAMING_LLM", True):
      with patch(f"{_STREAMING_MODULE}.litellm.get_model_info", side_effect=Exception("unknown")):
        with pytest.raises(StreamingNotSupportedError):
          require_streaming_capability("other", _TEST_MODEL)

  def test_optional_agent_name_stored_on_exception(self):
    with patch(f"{_STREAMING_MODULE}.ENSURE_STREAMING_LLM", True):
      with patch(f"{_STREAMING_MODULE}.litellm.get_model_info", return_value={"supports_native_streaming": False}):
        with pytest.raises(StreamingNotSupportedError) as exc_info:
          require_streaming_capability("", _TEST_MODEL)
        assert exc_info.value.agent_name == ""


class TestStreamingNotSupportedError:
  def test_exception_attributes(self):
    err = StreamingNotSupportedError(agent_name="a", model="m", message="msg")
    assert err.agent_name == "a"
    assert err.model == "m"
    assert err.message == "msg"
    assert str(err) == "msg"

