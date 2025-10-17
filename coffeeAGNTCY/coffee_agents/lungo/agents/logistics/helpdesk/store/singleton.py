# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from .memory import InMemoryOrderEventStore

# Singleton instance of the InMemoryOrderEventStore that is used by the streaming and A2A handler
global_store = InMemoryOrderEventStore()
