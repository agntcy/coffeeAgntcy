# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from config.config import LLM_MODEL
import litellm
from langchain_litellm import ChatLiteLLM

import common.chat_lite_llm_shim as chat_lite_llm_shim # our drop-in client

def get_llm():
  """
    Get the LLM provider based on the configuration using ChatLiteLLM
  """
  llm = ChatLiteLLM(model=LLM_MODEL)
  if LLM_MODEL.startswith("oauth2/"):
      llm.client = chat_lite_llm_shim
  return llm