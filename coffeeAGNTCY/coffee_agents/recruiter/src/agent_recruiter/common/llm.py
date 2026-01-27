# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from dotenv import load_dotenv
import os
import litellm
from agent_recruiter.common.logging import get_logger

load_dotenv()  # Load environment variables from .env file

logger = get_logger(__name__)

def configure_llm():
    # ============================================================================
    # LLM Configuration
    # ============================================================================
    # **LiteLLM**: Enables using various LLM providers with Google ADK.
    # See: https://docs.litellm.ai/docs/tutorials/google_adk

    LITELLM_PROXY_BASE_URL = os.getenv("LITELLM_PROXY_BASE_URL")
    LITELLM_PROXY_API_KEY = os.getenv("LITELLM_PROXY_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o")

    # Configure LiteLLM proxy if environment variables are set
    if LITELLM_PROXY_API_KEY and LITELLM_PROXY_BASE_URL:
        os.environ["LITELLM_PROXY_API_KEY"] = LITELLM_PROXY_API_KEY
        os.environ["LITELLM_PROXY_API_BASE"] = LITELLM_PROXY_BASE_URL
        logger.info(f"Using LiteLLM Proxy: {LITELLM_PROXY_BASE_URL}")
        litellm.use_litellm_proxy = True
    else:
        logger.info("Using direct LLM instance")