# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod

class IdentityService(ABC):
  """Interface for Identity Service commands."""

  @abstractmethod
  def connect_vault(self):
    pass

  @abstractmethod
  def generate_vault_key(self):
    pass

  @abstractmethod
  def register_issuer(self):
    pass

  @abstractmethod
  def generate_metadata(self):
    pass

  @abstractmethod
  def issue_badge(self):
    pass

  @abstractmethod
  def publish_badge(self):
    pass
