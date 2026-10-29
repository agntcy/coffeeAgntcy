# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Run limits, all overridable by environment variables (design D8, risks)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# Bumped when the moderator's turn structure changes, so every saved run says
# which scaffold produced it.
SCAFFOLD_VERSION = "1"

# <lungo>/runs/supply_chain, ignored by git (root .gitignore).
DEFAULT_RUN_ROOT = Path(__file__).resolve().parents[3] / "runs" / "supply_chain"


@dataclass(frozen=True)
class Limits:
    max_rounds: int = 6
    run_timeout: float = 900.0
    step_timeout: float = 120.0
    concord_threshold: float = 0.7
    concord_budget: int = 6

    def __post_init__(self) -> None:
        if self.max_rounds < 1:
            raise ValueError("SUPPLY_CHAIN_MAX_ROUNDS must be at least 1")
        if self.run_timeout <= 0 or self.step_timeout <= 0:
            raise ValueError("SUPPLY_CHAIN timeouts must be positive")
        if not 0 < self.concord_threshold <= 1:
            raise ValueError("SUPPLY_CHAIN_CONCORD_THRESHOLD must be in (0, 1]")
        if self.concord_budget < 1:
            raise ValueError("SUPPLY_CHAIN_CONCORD_BUDGET must be at least 1")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Limits:
        env = os.environ if env is None else env
        default = cls()
        return cls(
            max_rounds=int(env.get("SUPPLY_CHAIN_MAX_ROUNDS", default.max_rounds)),
            run_timeout=float(env.get("SUPPLY_CHAIN_RUN_TIMEOUT", default.run_timeout)),
            step_timeout=float(
                env.get("SUPPLY_CHAIN_STEP_TIMEOUT", default.step_timeout)
            ),
            concord_threshold=float(
                env.get("SUPPLY_CHAIN_CONCORD_THRESHOLD", default.concord_threshold)
            ),
            concord_budget=int(
                env.get("SUPPLY_CHAIN_CONCORD_BUDGET", default.concord_budget)
            ),
        )


def run_root_from_env(env: Mapping[str, str] | None = None) -> Path:
    env = os.environ if env is None else env
    configured = env.get("SUPPLY_CHAIN_RUN_DIR")
    return Path(configured) if configured else DEFAULT_RUN_ROOT
