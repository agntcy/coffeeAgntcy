# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from cnoe_agent_utils import LLMFactory

from config.config import LLM_PROVIDER

def get_llm():
  """
    Get the LLM provider based on the configuration using cnoe-agent-utils LLMFactory.
    """
  factory = LLMFactory(
    provider=LLM_PROVIDER,
  )
  return factory.get_llm()
