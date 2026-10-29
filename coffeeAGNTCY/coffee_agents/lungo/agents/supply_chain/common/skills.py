# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""The L9 deployment switch (SUPPLY_CHAIN_L9_ENABLED).

Only the baseline configuration runs today. The switch is read and validated
at start-up so that a deployment can already say whether L9 may run, but
turning it on changes nothing further: the L9 run types are not implemented.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

L9_ENV = "SUPPLY_CHAIN_L9_ENABLED"
_TRUE = frozenset({"1", "true", "yes", "on"})
_FALSE = frozenset({"0", "false", "no", "off"})


def l9_enabled(env: Mapping[str, str] | None = None) -> bool:
    """Whether this deployment may run ACCORD and CONCORD (design D12).

    Off when unset or empty: L9 has to be asked for. An unrecognized value
    raises instead of falling back to either side: the switch exists to prove
    that L9 is absent, so a typo must not silently leave it enabled.
    """
    env = os.environ if env is None else env
    raw = (env.get(L9_ENV) or "").strip().lower()
    if not raw or raw in _FALSE:
        return False
    if raw in _TRUE:
        return True
    raise ValueError(f"{L9_ENV} must be one of {sorted(_TRUE | _FALSE)}, got {raw!r}")
