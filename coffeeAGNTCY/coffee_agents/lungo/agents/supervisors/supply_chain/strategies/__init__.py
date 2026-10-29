# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Registry of negotiation strategies, one per configuration (design D4, D5)."""

from __future__ import annotations

from typing import Any

from agents.supervisors.supply_chain.strategies.l9_full import (
    NOT_IMPLEMENTED_MESSAGE,
    ConfigurationNotImplemented,
    L9FullStrategy,
)

IMPLEMENTED: frozenset[str] = frozenset({"baseline"})


def is_implemented(configuration: str) -> bool:
    return configuration in IMPLEMENTED


def get_strategy(configuration: str, **kwargs: Any):
    """Return the strategy for ``configuration``.

    ``kwargs`` carry what a strategy needs to talk to an LLM (an LLM
    factory). Unknown names raise ``ValueError``; ``l9_hybrid`` and
    ``l9_full`` raise ``ConfigurationNotImplemented``, so the runner reports
    ``not_implemented`` even when SUPPLY_CHAIN_L9_ENABLED is true.
    """
    if configuration == "l9_full":
        raise ConfigurationNotImplemented(NOT_IMPLEMENTED_MESSAGE)
    if configuration == "l9_hybrid":
        raise ConfigurationNotImplemented(
            "The l9_hybrid configuration is not implemented yet. Use baseline."
        )
    if configuration == "baseline":
        from agents.supervisors.supply_chain.strategies.baseline import (
            BaselineStrategy,
        )

        return BaselineStrategy(**kwargs)
    raise ValueError(f"unknown configuration {configuration!r}")


__all__ = [
    "NOT_IMPLEMENTED_MESSAGE",
    "ConfigurationNotImplemented",
    "L9FullStrategy",
    "get_strategy",
    "is_implemented",
]
