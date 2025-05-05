# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Literal, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings

# Error messages
INTERNAL_ERROR_MESSAGE = "An unexpected error occurred"

class Settings(BaseSettings):
  # Application settings
  API_V1_STR: str = "/api/v1"
  ENVIRONMENT: Literal["local", "staging", "production"] = "local"
  PROJECT_NAME: str = "Acorda Agent"
  DESCRIPTION: str = "Agent serving supervisor operations via natural language"

  # TODO: Keep these LLM-related env vars for now for validator purposes, but consider removing them in the future
  # Mandatory LLM settings
  LLM_PROVIDER: Optional[str] = "azure"  # or "openai"
  # OpenAI settings
  OPENAI_ENDPOINT: Optional[str] = None
  OPENAI_API_KEY: Optional[str] = None
  OPENAI_API_VERSION: Optional[str] = "gpt-4o"

  # Validate LLM settings
  @model_validator(mode="after")
  def check_required_settings(self) -> "Settings":
      logger = logging.getLogger(__name__)
      logger.info("Running model validator for Settings...")

      provider = self.LLM_PROVIDER.lower()
      if provider == "openai":
          missing = []
          if not self.OPENAI_ENDPOINT:
              missing.append("OPENAI_ENDPOINT")
          if not self.OPENAI_API_KEY:
              missing.append("OPENAI_API_KEY")
          if not self.OPENAI_API_VERSION:
              missing.append("OPENAI_API_VERSION")
          if missing:
              raise ValueError(
                  f"Missing required OpenAI environment variables: {', '.join(missing)}"
              )
      return self

  class Config:
      env_file = ".env"
      extra = "ignore"  # This will ignore any extra environment variables.

def get_settings_from_env() -> Settings:
    # This will load the settings from the environment variables
    return Settings()
