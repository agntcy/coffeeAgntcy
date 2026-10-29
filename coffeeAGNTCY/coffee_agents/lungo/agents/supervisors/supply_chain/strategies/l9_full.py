# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""``l9_full``: declared, not implemented (design Goals and Non-Goals).

In ``l9_full`` the L9 protocol is carried by the agents themselves, not by
the Buyer's code as in ``l9_hybrid``. Adding it later needs two things and
nothing else:

1. Initiator tools for the Buyer's LLM, wrapping an L9 bridge (the same
   wrapper ``l9_hybrid`` will use, neither exists yet), so the Buyer decides
   when to call ``init``, ``merge`` and ``decide`` and what to send.
2. Delegation tools, so the Buyer can address the other agents through
   ``Moderator.step`` from inside its tool loop.

The transport, the envelope, the record builder, the checker and the UI do
not change: a new ``Strategy`` that returns an ``Outcome`` is enough.
"""

from __future__ import annotations

from agents.supervisors.supply_chain.outcome import Outcome


class ConfigurationNotImplemented(Exception):
    """The requested configuration is declared but has no strategy yet."""


NOT_IMPLEMENTED_MESSAGE = (
    "The l9_full configuration is not implemented yet. Use baseline."
)


class L9FullStrategy:
    name = "l9_full"

    async def run(self, moderator) -> Outcome:  # noqa: ARG002
        raise ConfigurationNotImplemented(NOT_IMPLEMENTED_MESSAGE)
