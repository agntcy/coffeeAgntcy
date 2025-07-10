# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os

from cisco_outshift_agent_utils.llm_factory import LLMFactory
from config.config import LLM_PROVIDER

def get_llm():
  """
    Get the LLM provider based on the configuration using Cisco Outshift's LLMFactory.
    """
  factory = LLMFactory(
    provider=LLM_PROVIDER,
  )
  return factory.get_llm()