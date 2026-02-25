# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

import litellm

from config.config import ENSURE_STREAMING_LLM

logger = logging.getLogger(__name__)


class StreamingNotSupportedError(Exception):
  """Raised when the given LLM does not support streaming but the agent requires it."""

  def __init__(self, agent_name: str, model: str, message: str):
    self.agent_name = agent_name
    self.model = model
    self.message = message
    super().__init__(message)


def get_llm_streaming_capability(model: str) -> bool:
  """Return True only if the given LLM supports native streaming (LiteLLM static metadata)."""
  try:
    model_info = litellm.get_model_info(model=model)
    return model_info.get("supports_native_streaming") is True
  except (litellm.NotFoundError, litellm.BadRequestError, litellm.APIConnectionError, litellm.APIError, litellm.Timeout) as e:
    logger.debug("Could not get streaming capability for model %s: %s", model, e)
    return False
  except Exception as e:
    logger.debug("Unexpected error getting model info for %s: %s", model, e)
    return False


def require_streaming_capability(agent_name: str, model: str) -> None:
  """If ENSURE_STREAMING_LLM is true and the given LLM does not support streaming, log and raise StreamingNotSupportedError. agent_name and model are required."""
  if not ENSURE_STREAMING_LLM:
    return
  if not get_llm_streaming_capability(model):
    msg = (
      f"Configured model does not support streaming. "
      f"Set LLM_MODEL to a streaming-capable model (e.g. openai/gpt-4o)."
    )
    if agent_name:
      logger.error("[%s] %s Model: %s", agent_name, msg, model)
    else:
      logger.error("%s Model: %s", msg, model)
    raise StreamingNotSupportedError(agent_name=agent_name, model=model, message=msg)
  logger.info("[%s] Streaming capability check passed.", agent_name or "agent")
