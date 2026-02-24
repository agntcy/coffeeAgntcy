# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

import litellm

from config.config import LLM_MODEL, ENSURE_STREAMING_LLM

logger = logging.getLogger(__name__)


class StreamingNotSupportedError(Exception):
  """Raised when the configured LLM does not support streaming but the agent requires it."""

  def __init__(self, agent_name: str, model: str, message: str):
    self.agent_name = agent_name
    self.model = model
    self.message = message
    super().__init__(message)


def get_configured_llm_streaming_capability() -> bool:
  """Return True only if the configured LLM supports native streaming (LiteLLM static metadata)."""
  try:
    model_info = litellm.get_model_info(model=LLM_MODEL)
    return model_info.get("supports_native_streaming") is True
  except (litellm.NotFoundError, litellm.BadRequestError, litellm.APIConnectionError, litellm.APIError, litellm.Timeout) as e:
    logger.debug("Could not get streaming capability for model %s: %s", LLM_MODEL, e)
    return False
  except Exception as e:
    logger.debug("Unexpected error getting model info for %s: %s", LLM_MODEL, e)
    return False


def require_streaming_capability(agent_name: str = "") -> None:
  """If ENSURE_STREAMING_LLM is true and the configured LLM does not support streaming, log and raise StreamingNotSupportedError."""
  if not ENSURE_STREAMING_LLM:
    return
  if not get_configured_llm_streaming_capability():
    msg = (
      f"Configured model does not support streaming. "
      f"Set LLM_MODEL to a streaming-capable model (e.g. openai/gpt-4o)."
    )
    if agent_name:
      logger.error("[%s] %s Model: %s", agent_name, msg, LLM_MODEL)
    else:
      logger.error("%s Model: %s", msg, LLM_MODEL)
    raise StreamingNotSupportedError(agent_name=agent_name, model=LLM_MODEL or "", message=msg)
  logger.info("[%s] Streaming capability check passed.", agent_name or "agent")

