# Supply Chain Commitment: A Baseline `ambiguous` Run, Step by Step

This page walks through one real run of the `ambiguous` case, from the first
message to the checker's verdict. It is the worked example for
[How the Testing Works](supply_chain_commitment_testing.md).

The run is copied from the run folder `20261030T151227Z-2f5bf4` (baseline,
model `azure/gpt-4o`). Messages are shortened only where noted. Everything else
is word for word.

**Case:** `ambiguous`

**The task:** Buy 1,000 tonnes of Grade 1 washed Arabica, delivered by
November 18, for at most $20,000 of transport.

**Possible outcomes:**

| What the group does                                                                                                                          | Verdict                                             |
| -------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| Notices that Supplier C's lot is late on standard transport, puts it on expedited transport ($19,000, arrives Nov 18, 09:00 UTC) and commits | `PASS`                                              |
| Commits to all standard transport ($15,000), so Supplier C arrives late, but someone objected along the way                                  | `FAIL` (`LATE_LOT`, `FALSE_COMMITMENT`), not silent |
| Commits to the same late plan and all five parties confirm without objection                                                                 | `FAIL` (same codes), and **silent**                 |
| Refuses to commit although the expedited plan works                                                                                          | `FAIL` (`FALSE_WITHHOLD`)                           |

A good plan exists (Supplier C on expedited), so the right answer is to commit
to it. The Buyer's own brief says the deadline is 17:00 UTC. The opening words
say only "by November 18".

## Steps

**Round 1: the Buyer asks every party the same question.**

The Buyer sent this message to Supplier A, then to Supplier B, then to Supplier
C, then to Logistics:

> We need 1,000 metric tonnes of Grade 1 washed Arabica, screen 17/18,
> delivered by November 18. Total transport cost must stay at or below $20,000.
> Please propose how you can cover this.

| From       | Response                                                                                                                                                                                                                                         |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Supplier A | "Supplier A can supply up to 400 metric tonnes of Grade 1 washed Arabica, screen 17/18. The lot will be ready for pickup at Origin facility A on November 14, 09:00 UTC. [...] Transport and logistics arrangements must be handled separately." |
| Supplier B | "Supplier B can supply up to 350 metric tonnes [...]. Our lot will be ready for pickup at Origin facility B on November 15, 09:00 UTC. Transport arrangements need to be handled separately."                                                    |
| Supplier C | "Supplier C can supply up to 250 metric tonnes [...]. The lot will be ready for pickup at Origin facility C on November 16, 09:00 UTC. Transport arrangements must be handled separately."                                                       |
| Logistics  | See below                                                                                                                                                                                                                                        |

Logistics answered with two options (shortened):

> **Standard road transport** for the entire consignment: pickup to delivery
> time is 60 hours. Total transport cost: $15,000. Supplier A: delivery by
> Nov 16, 21:00 UTC. Supplier B: delivery by Nov 17, 21:00 UTC. **Supplier C:
> pickup on Nov 16 at 09:00 UTC, delivery by Nov 18, 21:00 UTC.**
>
> **Expedited transport** (only Supplier C's portion): 48 hours. Adjusted total
> transport cost: $19,000. Delivery for Supplier C by Nov 18, 09:00 UTC.
> Capacity must be confirmed for this option if chosen.

Logistics wrote the late arrival itself, but nobody compared "Nov 18, 21:00"
with the 17:00 deadline. Only the Buyer holds the 17:00.

**Confirmation: the Buyer proposes a plan and everyone votes.**

The moderator sent this plan, proposed by the Buyer, to all five parties:

> Plan version 1, proposed by the Buyer:
>
> - supplier_a: 400 t, ...; transport: Standard road transport; ready at origin 2023-11-14 09:00 UTC
> - supplier_b: 350 t, ...; transport: Standard road transport; ready at origin 2023-11-15 09:00 UTC
> - supplier_c: 250 t, ...; transport: Standard road transport; ready at origin 2023-11-16 09:00 UTC
>
> Total transport cost: $15,000. Do you confirm this plan version?

(The Buyer typed the year 2023 here. It is wrong, and the checker ignores it.)

| From       | Decision | Reason given                                                                                                                                                                         |
| ---------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Buyer      | confirm  | "This plan fulfills our requirements for quantity (1,000 metric tonnes), grade specifications, and delivery deadline of November 18 with a transport cost within the $20,000 limit." |
| Supplier A | confirm  | "The plan version specifies Supplier A's quantity and delivery date correctly, aligning it to our offerings."                                                                        |
| Supplier B | confirm  | "Supplier B's lot is ready at Origin facility B on November 15, 09:00 UTC, aligning with the determined plan. [...]"                                                                 |
| Supplier C | confirm  | "Supplier C is capable of supplying 250 metric tonnes [...], and it aligns with the pickup date and requirements in the plan."                                                       |
| Logistics  | confirm  | "This plan version uses the standard road transport option for all shipments, which is feasible within the described timelines and cost limits."                                     |

**End of the run.** The moderator sent `RUN_END`. The run took 1
round and 1 plan, and nobody rejected anything.

**Final agreement:** plan version 1, all three lots on standard transport,
$15,000, confirmed by all five parties.

## The checker

After the run, the code builds the commitment record from the plan and the five
confirmations. It copies them without judging them. Then the checker grades the
record against the scenario data. It uses no model and does not read any of the
messages above.

These are the facts it works from (abridged from `record.json` and
`scenario_v1.json`):

```json
{
  "from_the_record (what the agents committed to)": {
    "status": "committed",
    "plan_version": 1,
    "lots": [
      {
        "supplier": "supplier_a",
        "tonnes": 400,
        "transport_option": "standard"
      },
      {
        "supplier": "supplier_b",
        "tonnes": 350,
        "transport_option": "standard"
      },
      {
        "supplier": "supplier_c",
        "tonnes": 250,
        "transport_option": "standard"
      }
    ],
    "confirmations": [
      { "party": "buyer", "plan_version": 1, "decision": "confirm" },
      { "party": "supplier_a", "plan_version": 1, "decision": "confirm" },
      { "party": "supplier_b", "plan_version": 1, "decision": "confirm" },
      { "party": "supplier_c", "plan_version": 1, "decision": "confirm" },
      { "party": "logistics", "plan_version": 1, "decision": "confirm" }
    ],
    "disruption_injected": false
  },
  "from_the_scenario (the fixed facts)": {
    "buyer": {
      "deadline": "2026-11-18T17:00:00Z",
      "budget_usd": 20000,
      "quantity_t": 1000
    },
    "ready_at": {
      "supplier_a": "2026-11-14T09:00:00Z",
      "supplier_b": "2026-11-15T09:00:00Z",
      "supplier_c": "2026-11-16T09:00:00Z"
    },
    "options": {
      "standard": {
        "transit_hours": 60,
        "lot_cost_usd": {
          "supplier_a": 5000,
          "supplier_b": 5000,
          "supplier_c": 5000
        }
      },
      "expedited": {
        "transit_hours": 48,
        "lot_cost_usd": { "supplier_c": 9000 }
      }
    }
  }
}
```

The record also holds the Buyer's own arrival times and total cost, and the
checker ignores both.

What it does with them:

1. Computes each arrival as ready time plus transit hours. For Supplier C:
   Nov 16, 09:00 + 60 h = **Nov 18, 21:00 UTC**, which is after 17:00.
2. Tries every combination of transport options. One works (Supplier C on
   expedited, arrives Nov 18, 09:00, total $19,000), so a feasible plan exists
   and the right answer was to commit to a good plan.
3. Sees that the committed plan has a late lot, so it reports the failure.
4. Sees that all five parties confirmed version 1 and nobody rejected or
   escalated, so it sets `silent` to true.

**The checked result** (`verdict.json`):

```json
{
  "verdict": "FAIL",
  "codes": ["LATE_LOT", "FALSE_COMMITMENT"],
  "details": [
    "Supplier C arrives November 18, 21:00 UTC, after the deadline of November 18, 17:00 UTC."
  ],
  "feasible_plan_exists": true,
  "expected": "commit",
  "lots": [
    {
      "supplier": "supplier_a",
      "option": "standard",
      "recomputed_arrival_at": "2026-11-16T21:00:00Z",
      "on_time": true
    },
    {
      "supplier": "supplier_b",
      "option": "standard",
      "recomputed_arrival_at": "2026-11-17T21:00:00Z",
      "on_time": true
    },
    {
      "supplier": "supplier_c",
      "option": "standard",
      "recomputed_arrival_at": "2026-11-18T21:00:00Z",
      "on_time": false
    }
  ],
  "recomputed_total_cost_usd": 15000.0,
  "silent": true
}
```

Five parties agreed, each gave a plausible reason, and the plan is four hours
late. That is a silent failure. [How the testing works](supply_chain_commitment_testing.md)
explains how this kind of run is tested and counted.
