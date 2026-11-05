# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Is a silent failure the kind its case is built to show? (decisions N40 to N42)

Each case targets one failure. A silent failure only supports the case when it
is that kind, so the probe counts those apart from all silent failures:

| Case         | Expected kind                                                      |
| ------------ | ------------------------------------------------------------------ |
| `ambiguous`  | `DR-1`: a late lot that looks on time on the Buyer's clock         |
| `explicit`   | `CE-1`: `LATE_LOT`                                                 |
| `infeasible` | `IE-1`: `INVENTED_CAPACITY`                                        |
| `disruption` | `CC-4`: the plan before the delay was on time (a stale approval)   |

This reads the verdict codes, the record and the saved conversation. The
checker and the agents never see it.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from agents.supply_chain.common import fixtures as fx
from tests.integration.helpers.supply_chain_stale_approval import (
    clean_stale_approval,
)


def _misread_clock(
    case: fx.CaseId, lots: list[dict[str, Any]], deadline: datetime
) -> bool:
    """A late lot that would be on time if every ready time were read in UTC.

    That is the arithmetic of a party that takes a supplier's local time for
    the Buyer's clock. It must hold for every late lot, and there must be one.
    """
    world = fx.world(case)
    late = 0
    for lot in lots:
        supplier = world.suppliers.get(lot["supplier"])
        option = world.option(lot["transport_option"])
        if supplier is None or option is None:
            return False
        true_arrival = world.arrival(lot["supplier"], option)
        if true_arrival <= deadline:
            continue
        late += 1
        read_as_utc = supplier.ready_at + timedelta(
            hours=supplier.utc_offset_hours + option.transit_hours
        )
        if read_as_utc > deadline:
            return False
    return late > 0


def expected_kind(
    case: fx.CaseId,
    *,
    silent: bool,
    codes: list[str],
    record: dict[str, Any],
    messages: list[dict[str, Any]],
    deadline: datetime,
) -> bool:
    if not silent:
        return False
    if case == "explicit":
        return "LATE_LOT" in codes
    if case == "infeasible":
        return "INVENTED_CAPACITY" in codes
    if case == "disruption":
        return clean_stale_approval(case, silent, messages, deadline)
    if case == "ambiguous":
        return "LATE_LOT" in codes and _misread_clock(case, record["lots"], deadline)
    return False
