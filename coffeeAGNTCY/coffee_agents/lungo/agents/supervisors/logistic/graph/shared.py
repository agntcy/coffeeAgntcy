# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional
from agntcy_app_sdk.factory import AgntcyFactory

_factory: Optional[AgntcyFactory] = None

def set_factory(factory: AgntcyFactory):
    global _factory
    _factory = factory

def get_factory() -> AgntcyFactory:
    if _factory is None:
        return AgntcyFactory("lungo.logistic", enable_tracing=True)
    return _factory
