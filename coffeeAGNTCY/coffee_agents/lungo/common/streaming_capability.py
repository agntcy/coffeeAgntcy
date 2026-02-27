# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

import litellm

import config.config as _config

logger = logging.getLogger(__name__)


class StreamingNotSupportedError(Exception):
  """Raised when the given LLM does not support streaming but the agent requires it."""

  def __init__(self, agent_name: str, model: str, message: str):
    self.agent_name = agent_name
    self.model = model
    self.message = message
    super().__init__(message)


def get_llm_streaming_capability(model: str) -> tuple[bool, BaseException | None]:
  """Return (True, None) if the given LLM supports native streaming; (False, None) if metadata says no or key missing; (False, e) if an error occurred, with e the original exception."""
  try:
    model_info = litellm.get_model_info(model=model)
    if model_info.get("supports_native_streaming") is True:
      return (True, None)
    return (False, None)
  except (litellm.NotFoundError, litellm.BadRequestError, litellm.APIConnectionError, litellm.APIError, litellm.Timeout) as e:
    logger.debug("Could not get streaming capability for model %s: %s", model, e)
    return (False, e)
  except Exception as e:
    logger.debug("Unexpected error getting model info for %s: %s", model, e)
    return (False, e)


def require_streaming_capability(agent_name: str, model: str) -> None:
  """If ENSURE_STREAMING_LLM is true and the given LLM does not support streaming, log and raise StreamingNotSupportedError. agent_name and model are required."""
  if not _config.ENSURE_STREAMING_LLM:
    return
  supported, err = get_llm_streaming_capability(model)
  if supported:
    logger.info("[%s] Streaming capability check passed.", agent_name or "agent")
    return
  msg = (
    f"Configured model does not support streaming. "
    f"Set LLM_MODEL to a streaming-capable model (e.g. openai/gpt-4o)."
  )
  if err is not None:
    if agent_name:
      logger.error("[%s] %s Model: %s (cause: %s)", agent_name, msg, model, err)
    else:
      logger.error("%s Model: %s (cause: %s)", msg, model, err)
    raise StreamingNotSupportedError(agent_name=agent_name, model=model, message=msg) from err
  if agent_name:
    logger.error("[%s] %s Model: %s", agent_name, msg, model)
  else:
    logger.error("%s Model: %s", msg, model)
  raise StreamingNotSupportedError(agent_name=agent_name, model=model, message=msg)
