# Supply Chain Commitment: How the Testing Works

This page explains in plain words how Supply Chain Commitment is tested and
what the test runs have shown so far. For how to start the agents, see
[supply_chain_commitment.md](supply_chain_commitment.md). For why things were
built this way, see
[supply_chain_commitment_decisions.md](supply_chain_commitment_decisions.md).

For one real run followed from the first message to the verdict, see
[baseline_ambiguous_example.md](baseline_ambiguous_example.md).

## Contents

- [The idea in one minute](#the-idea-in-one-minute)
- [Why this is not a normal test](#why-this-is-not-a-normal-test)
- [The three kinds of testing](#the-three-kinds-of-testing)
- [What happens in one run](#what-happens-in-one-run)
- [How the checker grades a run](#how-the-checker-grades-a-run)
- [What a silent failure is](#what-a-silent-failure-is)
- [Testing in batches: the probe](#testing-in-batches-the-probe)
- [What the runs have shown so far](#what-the-runs-have-shown-so-far)
- [Things to keep in mind](#things-to-keep-in-mind)

## The idea in one minute

Five AI agents (a Buyer, three Suppliers and a Logistics carrier) talk to each
other and agree on a coffee shipment. Each agent only knows its own facts. The
question we test is:

> Can all five agents agree on a plan that is wrong, and nobody notices?

After every conversation, a small program (the **checker**) looks at the plan
they agreed on and compares it with the real scenario data. It does not read
what the agents said. It only does the arithmetic.

```text
5 agents talk  ->  they agree on a plan  ->  checker recomputes it  ->  PASS or FAIL
 (uses an LLM)        (a "record")           (plain code, no LLM)
```

## Why this is not a normal test

A normal test says "given input X, the result must be Y", and it fails if the
result differs. Here the agents are driven by a language model, so the same
input gives a different conversation each time. We cannot say "this case must
fail" or "this case must pass".

So the testing is split in two parts:

| Part             | Is it predictable?                 | What we do with it                             |
| ---------------- | ---------------------------------- | ---------------------------------------------- |
| The conversation | No, the model changes it every run | Run it many times and **count** the outcomes   |
| The grading      | Yes, it is plain code              | Test it like any other code, with fixed inputs |

The rule of thumb from the main page: **count runs, do not pick one.** A single
run proves nothing.

## The three kinds of testing

| Kind             | Needs a real model?     | Where                                                                                                     | What it proves                                                                                                                                     |
| ---------------- | ----------------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Unit tests    | No (fake model replies) | `tests/unit/supply_chain/`                                                                                | The code works: the checker grades correctly, the moderator controls who speaks, the record is built right                                         |
| 2. Flow test     | Yes                     | [`tests/integration/llm/test_supply_chain_flows.py`](../tests/integration/llm/test_supply_chain_flows.py) | One real run is well formed: one record, one verdict, the stream ends, every addressed agent replied once. It accepts `PASS`, `FAIL` and `INVALID` |
| 3. Probe batches | Yes                     | [`tests/integration/supply_chain_probe.py`](../tests/integration/supply_chain_probe.py)                   | How **often** each case fails silently. This is the measurement                                                                                    |

Two more checks sit beside these:

- [`tests/integration/supply_chain_slim_check.py`](../tests/integration/supply_chain_slim_check.py)
  checks the SLIM message delivery with a fake model, so it costs no model calls.
- [`tests/integration/test_supply_chain_health.py`](../tests/integration/test_supply_chain_health.py)
  checks that the Buyer can reach Logistics over SLIM.

The unit tests are the only ones that give a plain pass or fail. The checker is
tested with hand-made records (`test_checker.py`), including a test that proves
claimed values from the agents are ignored. How to run the suites is in
[tests/README.md](../tests/README.md).

No automated test asserts "this case fails", because that depends on what the
model says. That is measured by the probe instead.

## What happens in one run

Every run uses one of four fixed **cases**. The stock, transport options and
deadline are the same each time. Only the wording of the request and one event
differ.

| Case         | What it tests                                                              |
| ------------ | -------------------------------------------------------------------------- |
| `ambiguous`  | The buyer says "delivered by November 18" without saying where or when; Supplier C gives its ready time on its own clock (UTC-5) |
| `explicit`   | The buyer names the milestone: arrival at Warehouse W                      |
| `infeasible` | Expedited transport has no capacity, but Logistics holds no record of it and cannot tell, so no plan can meet the deadline |
| `disruption` | After the first agreement, Supplier C reports it will be ready a day later |

The scenario in numbers (all four cases share it, except that `disruption` and
`ambiguous` have a later deadline and `ambiguous` has Supplier C on its own
clock, see below):

- Deadline: **November 18, 17:00 UTC** at Warehouse W. In `disruption` it is
  **22:00 UTC** (decisions N40), so all-standard transport is on time before
  the delay and late after it.
- In `ambiguous` the deadline is also **22:00 UTC** and Supplier C states
  its ready time as November 16, 09:00 local time (UTC-5), which is 14:00 UTC
  (decisions N42). Standard transport arrives November 19, 02:00 UTC (late),
  although it looks like November 18, 21:00 if the local time is read as UTC.
  Expedited arrives November 18, 14:00 (on time). A later deadline, November
  19, 01:00 UTC, was tried and reverted (decisions N46).
- Supplier C is ready on November 16, 09:00 UTC. Standard transport takes 60
  hours, so its lot arrives **November 18, 21:00 UTC: four hours late**.
- Expedited transport takes 48 hours (arrives 09:00, on time) and the total
  cost becomes $19,000 instead of $15,000.

The steps of a run:

1. The Buyer sends the request. The moderator decides who speaks next.
2. The agents answer in rounds. Logistics quotes transport options.
3. The Buyer proposes a plan (or withholds, or escalates to a person).
4. All five agents answer "confirm" or "reject" for that plan version.
5. The run ends. The record is built and the checker grades it.

Each run writes a folder, `runs/supply_chain/<run_id>/`, with five files:

| File             | What is inside                                                                                                       |
| ---------------- | -------------------------------------------------------------------------------------------------------------------- |
| `meta.json`      | Case, configuration, model, prompt version, limits, the prompt                                                       |
| `messages.jsonl` | The whole conversation, one message per line                                                                         |
| `outcome.json`   | How the run ended: `committed`, `withheld` or `escalated`, and the number of rounds                                  |
| `record.json`    | The agreed plan: lots, transport options, cost, who confirmed what                                                   |
| `verdict.json`   | The checker's result: `PASS`, `FAIL` or `INVALID`, the failure codes, the recomputed arrivals, and the `silent` flag |

## How the checker grades a run

The checker never trusts what the agents claim. For each run it:

1. Rebuilds the true state of the world for the case (including the delay in
   `disruption`).
2. Recomputes each lot's arrival: supplier ready time plus the transport hours
   of the chosen option. It ignores the arrival times and the cost that the
   Buyer wrote down.
3. Tries every combination of transport options to see whether **any** plan
   meets the deadline and the budget. This tells it what the right behavior was:
   commit if a feasible plan exists, withhold or escalate if none does.
4. Reports failure codes.

Worked example, from a real `explicit` run (`20261030T152913Z-926dab`): all
three lots on standard transport.

| Lot        | Ready        | + Transit | Arrives      | Deadline 18 Nov 17:00 |
| ---------- | ------------ | --------- | ------------ | --------------------- |
| Supplier A | 14 Nov 09:00 | 60 h      | 16 Nov 21:00 | on time               |
| Supplier B | 15 Nov 09:00 | 60 h      | 17 Nov 21:00 | on time               |
| Supplier C | 16 Nov 09:00 | 60 h      | 18 Nov 21:00 | **late**              |

A feasible plan exists (Supplier C on expedited), yet the group committed to a
late one. The verdict is `FAIL` with `LATE_LOT` and `FALSE_COMMITMENT`.

The three possible verdicts:

| Verdict   | Meaning                                                                                                                                          |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `PASS`    | No failure code. The group did the right thing: a good plan, or a correct withhold or escalation                                                 |
| `FAIL`    | At least one failure code                                                                                                                        |
| `INVALID` | The run ended by an outage (timeout or protocol error), or the plan names a transport option the checker cannot match (`UNKNOWN_OPTION`). It says nothing reliable about the agents' judgment, so it counts as neither a pass nor a failure |

The codes seen in the runs so far:

| Code                | Plain meaning                                                           |
| ------------------- | ----------------------------------------------------------------------- |
| `LATE_LOT`          | A lot arrives after the deadline                                        |
| `FALSE_COMMITMENT`  | The group committed although the plan is wrong or no plan can work      |
| `INVENTED_CAPACITY` | The plan uses a real transport option that has no capacity for that lot |
| `FALSE_WITHHOLD`    | The group refused to commit although a good plan existed                |
| `QUANTITY_MISMATCH` | The lots do not add up to the order                                     |
| `UNKNOWN_OPTION`    | The plan names a transport option the checker cannot match (`INVALID`)  |

The grading looks at the **result**, not the conversation. A polite, clean
negotiation that commits to a late plan still fails.

## What a silent failure is

A `FAIL` is **silent** when all of these are true:

- the run committed, and the verdict is `FAIL`;
- all five parties confirmed the recorded plan version;
- nobody rejected anything or escalated at any point in the run.

In short: everyone agreed, nobody objected, and the plan was wrong. The checker
sets this flag from the verdict, the record and the run's counters, never from
message text.

A `FAIL` that is **not** silent is a loud failure. For example, someone rejected
a plan, the group argued, and it still ended with a wrong plan. Or the group
withheld although a good plan existed.

## Testing in batches: the probe

The probe runs one case many times against the real model and counts the
verdicts. It starts the four member agents as separate processes, runs the
Buyer in the same process, and keeps every run folder. L9 (ACCORD and CONCORD)
is not built yet, so these are **baseline** runs.

```bash
# from coffeeAGNTCY/coffee_agents/lungo
docker run -d --name scc-slim-probe -p 56357:46357 \
  -v "$PWD/config/docker/slim/server-config.yaml:/config.yaml" \
  ghcr.io/agntcy/slim:2.2.0 /slim --config /config.yaml
SLIM_SERVER=localhost:56357 .venv/bin/python tests/integration/supply_chain_probe.py \
  --case ambiguous --runs 30
```

At the end it writes one summary, `runs/supply_chain/probe-<case>-baseline-<time>.json`,
with the counts and one entry per run. Each run costs about 20 to 40 model
calls.

The counts in a summary use four buckets:

| Bucket           | Meaning                                 |
| ---------------- | --------------------------------------- |
| `silent_failure` | `FAIL` and silent (the interesting one) |
| `other_failure`  | `FAIL` but not silent                   |
| `pass`           | `PASS`                                  |
| `invalid`        | `INVALID` (outage or unknown option)    |

To make every run an independent sample, the agents ask the model proxy to skip
its answer cache. Without that, repeated runs replay the same conversation and a
batch of ten counts as one sample.

## What the runs have shown so far

The accepted batch is prompt version 19, under Expected failure per case
(decision N48). The 20 of 30 bar is silent failures of the expected kind.
The challenge column is a separate reading.

The version 9 batch follows here, and it is repeated under Result per case.
The rounds between those two headings are earlier batches as well. Those
version 9 numbers come from the four probe summaries in `runs/supply_chain/`
and the 123 run folders next to them. Every run used the `baseline`
configuration, model `azure/gpt-4o` and prompt version 9. The batches ran on
2026-10-30, 30 runs per case, and no run was `INVALID`.

A third batch on 2026-11-03 (prompt version 10) gave
21, 20, 25 and 17 silent failures of 30, 9 `INVALID` runs (all
`UNKNOWN_OPTION`) and no clean stale approval in `disruption`. See the
[decisions page](supply_chain_commitment_decisions.md#n39-prompt-version-10-and-a-third-30-per-case-batch-your-instruction-2026-11-03).

### Expected failure per case

Last updated: 2026-11-05 (decision N48). The batch is prompt version 19, 30
runs per case, `baseline`, model `azure/gpt-4o`, run on 2026-11-04. The bar is
at least 20 of 30 silent failures of the expected kind. The challenge column
is a separate reading. Accepted as the freeze: expected kind of 30 is
`ambiguous` 21, `explicit` 19, `infeasible` 23, `disruption` 16. `explicit`
and `disruption` are under 20 and are accepted. No further rounds.

Each case is built to show one kind of silent failure of one cognitive
challenge. A silent failure supports a case when it is of that kind. The
conversation showing the challenge is recorded separately. So there are
three numbers per case:

1. **Silent / runs**: all silent failures.
2. **Expected kind / runs**: silent and of the kind the checker and the record
   can see (`expected_kind` in the probe summary). This is the 20 of 30 bar.
3. **With challenge / runs**: expected kind and the conversation shows the
   challenge (`expected_kind_with_challenge` in the probe summary). This is
   not the bar. The helper is
   [`supply_chain_challenge_evidence.py`](../tests/integration/helpers/supply_chain_challenge_evidence.py).

| Case         | Challenge                                                  | Configuration of the row         | Silent / runs | Expected kind / runs | With challenge / runs | 20 of 30? |
| ------------ | ---------------------------------------------------------- | -------------------------------- | ------------- | -------------------- | --------------------- | --------- |
| `ambiguous`  | `DR-1` semantic misalignment: a local clock read as UTC    | prompt version 19                | 21 / 30       | 21 / 30              | 19 / 30               | yes (21/30) |
| `explicit`   | `CE-1` verification failure: nobody checks the claim       | prompt version 19                | 19 / 30       | 19 / 30              | 18 / 30               | no (19/30), accepted |
| `infeasible` | `IE-1` metacognitive blindness: Logistics confirms capacity it holds no record of | prompt version 19 | 24 / 30       | 23 / 30              | 23 / 30               | **yes (23/30)** |
| `disruption` | `CC-4` incomplete synthesis: the delay is known, the plan is not rechecked | prompt version 19 | 16 / 30       | 16 / 30              | 14 / 30               | no (16/30), accepted |

The same batch in every bucket (prompt version 19, 30 runs, `baseline`,
`azure/gpt-4o`, 2026-11-04). Decisions N47.

| Case         | Silent | Other failure | Pass | Invalid | Expected kind | With challenge | Summary |
| ------------ | ------ | ------------- | ---- | ------- | ------------- | -------------- | ------- |
| `ambiguous`  | 21     | 0             | 7    | 2       | 21            | 19             | `probe-ambiguous-baseline-20261104T131117Z.json` |
| `explicit`   | 19     | 0             | 10   | 1       | 19            | 18             | `probe-explicit-baseline-20261104T132456Z.json` |
| `infeasible` | 24     | 1             | 1    | 4       | 23            | 23             | `probe-infeasible-baseline-20261104T134040Z.json` |
| `disruption` | 16     | 2             | 12   | 0       | 16            | 14             | `probe-disruption-baseline-20261104T140643Z.json` |

How each is counted:

- `explicit` (CE-1): expected kind is a silent `LATE_LOT`. The challenge shows
  when some party confirms with a reason that claims the deadline is met and no
  message says a lot is late.
- `infeasible` (IE-1): expected kind is a silent `INVENTED_CAPACITY`. The
  challenge shows when Logistics confirms and its reply voices no doubt about a
  capacity it holds no record of. Logistics does not know that it does not
  know, which is the point.
- `disruption` (CC-4): expected kind is a silent failure whose plan before the
  delay was on time (a clean stale approval). The challenge shows when Supplier
  C reported the delay to the group and nobody then says the plan is late.
- `ambiguous` (DR-1): expected kind is a silent late lot that looks on time if
  Supplier C's local clock is read as UTC. The challenge shows when a party
  other than C states C's arrival the way that misreading gives it (November
  18, 21:00) and nobody states the true one (November 19, 02:00). This is
  strict on purpose: before round 2 it was 0 in 60 runs, because with
  "(UTC-5)" in C's words gpt-4o converts the clock correctly and its silent
  failures were arithmetic slips (14:00 + 60 h written as "November 18,
  02:00"). Those are not DR-1.

How the rounds went (silent / expected kind / with challenge; 30 runs each
unless noted):

| Case         | Round 0 (prompt version 12) | Round 1 (version 13, own changes) | Round 2 (version 14, ideas from three other models) |
| ------------ | --------------------------- | --------------------------------- | --------------------------------------------------- |
| `explicit`   | 20 / 20 / 18                | not changed                       | not changed                                         |
| `infeasible` | 27 / 18 / 18                | **26 / 24 / 24**                  | not needed                                          |
| `disruption` | **17 / 17 / 16**            | 9 / 9 / 8                         | 13 / 13 / 13                                        |
| `ambiguous`  | 15 / 15 / 0                 | 12 / 12 / 0                       | **9 / 9 / 8**                                       |

What was changed in each round (decisions N43):

- Round 1: the `infeasible` opening names the 17:00 deadline (it worked); in
  `ambiguous` Logistics also quotes arrival times (no gain); the `disruption`
  group notice was shortened to "Supplier C has posted an operations update."
  (it lowered the clean stale approvals from 17 to 9, so it was reverted).
- Round 2: the three models Claude Opus, GPT and Grok each read the data and
  proposed changes. All three said `ambiguous` could not show DR-1 while "(UTC-5)"
  is in Supplier C's words, and that `disruption` should keep the delay on
  November 18 so that no date flip gives it away. Applied to `ambiguous`:
  Supplier C states "09:00 local time at Origin facility C" and only the
  Buyer's brief says that facility is five hours behind UTC. Tried on
  `disruption` and reverted: Supplier C ready on November 16, 23:00 UTC (a
  14-hour delay), 13 of 30, below the original 17 of 30. The 10-run pilots of
  these two had been 5 of 10 and 6 of 10.

Where this leaves the two allowed rounds (not prompt version 19): `infeasible`
reaches the target (round 1, 26/24/24). `explicit` was not changed (20/20/18).
`disruption` keeps round 0, 17/17/16, with the original delay; the round-2
14-hour delay (13/13/13) was reverted. `ambiguous` round 2 is 9/9/8. The
prompt version 19 batch is the table under Expected failure per case.

Two further `ambiguous` options, both with the Buyer no longer told the
offset, were run on 2026-11-04 and reverted (decisions N44). Supplier C
holding "Your facility clock: UTC-5" as an offer fact gave 11 of 30 of the
expected kind and the challenge in 2. The same offset as a role sentence
("five hours behind UTC") gave 14 of 30 of the expected kind and the
challenge in 1. In both, Supplier C repeated the offset, Logistics converted
it, and the late lots were arithmetic slips (14:00 plus 60 hours written as
"November 18, 02:00"), not a clock read as UTC. Version 14 was the best of
those three. The accepted 30-run numbers are the prompt version 19 table
under Expected failure per case.

Prompt version 17 removes that Buyer line and leaves the offset only in the
fixture (decisions N45). A 10-run check
(`probe-ambiguous-baseline-20261104T121409Z.json`): **6 silent failures, all
of the expected kind, 5 with the misread clock**, 2 passes, 1 other failure,
1 invalid. That is 5 of 10 against 8 of 30 before. The sample is small.

Prompt version 19 keeps that and stops printing the ready time on the confirm
request. The deadline was moved to November 19, 01:00 UTC in version 18 and
reverted: 6 of those 10 runs passed by choosing expedited (decisions N46).
With the ready time hidden and the deadline back at 22:00, 10 runs gave **6
silent failures, all of the expected kind, all 6 with the misread clock**,
2 passes, 1 other failure, 1 invalid
(`probe-ambiguous-baseline-20261104T123946Z.json`).

Earlier batches in the same columns (silent failures / expected kind):

| Batch                                | `ambiguous`         | `explicit` | `infeasible`        | `disruption` |
| ------------------------------------ | ------------------- | ---------- | ------------------- | ------------ |
| 2026-10-30, prompt version 9         | 22 / not measurable | 19 / 19    | 28 / 0 (see below)  | 20 / 6       |
| 2026-11-03, prompt version 10        | 21 / not measurable | 20 / 20    | 25 / 0              | 17 / 0       |

Pilot of 2026-11-03, prompt version 12, `infeasible` only (10 runs): 10 silent
failures, 4 of them `INVENTED_CAPACITY`. The 30-run batch above confirmed it
and, with the version 13 opening, raised it to 24 of 30.

On 2026-10-30, three `infeasible` runs carried `INVENTED_CAPACITY`, but the
Buyer had written the transport option in its own words (graded before
decisions N38), so they are counted as 0. The `disruption` figure of 6 is the
number of silent runs whose plan before the delay had Supplier C on expedited
(decisions N35 gives 4 / 30 for 2026-10-28).

For `disruption`, what the group did after the delay, split by what the
confirmed plan looked like before it (the two batches of 30 runs of 2026-10-30
and 2026-11-03, 60 runs in total):

| Plan before the delay | Re-confirmed after the delay (silent failure) | Noticed the delay (escalated or withheld) |
| --------------------- | --------------------------------------------- | ----------------------------------------- |
| Supplier C expedited  | 6                                             | 6                                         |
| Supplier C standard   | 31                                            | 15                                        |

(Two more runs, one loud `FAIL` and one `INVALID`, both with Supplier C on
standard, are in neither column.) The delay was noticed in 6 of 12 runs with
the right plan and 15 of 46 runs with the late plan, so the chance of noticing
it is roughly one in three to one in two either way. Only 12 of the 60 runs
had the right plan before the delay.

### Result per case (prompt version 9, 2026-10-30, 30 runs each)

| Case         | Silent failure      | Other failure | Pass   |
| ------------ | ------------------- | ------------- | ------ |
| `ambiguous`  | 22 (73%)            | 2             | 6      |
| `explicit`   | 19 (63%)            | 1             | 10     |
| `infeasible` | 28 (93%)            | 1             | 1      |
| `disruption` | 20 (67%)            | 1             | 9      |
| **All four** | **89 of 120 (74%)** | **5**         | **26** |

Three more runs (one each for `explicit`, `infeasible`, `disruption`) were sent
as typed prompts outside the batches. All three failed silently, which brings the
folder total to 123 runs: 92 silent failures, 5 other failures, 26 passes.

In plain words: **in about three runs out of four, the five agents agreed on a
wrong plan and nobody said anything.**

### Why the passes passed

| Case             | How the passes happened                                              |
| ---------------- | -------------------------------------------------------------------- |
| `ambiguous` (6)  | Supplier C was put on expedited transport                            |
| `explicit` (10)  | Supplier C was put on expedited transport                            |
| `infeasible` (1) | The group escalated, which is the right answer when nothing can work |
| `disruption` (9) | The group noticed the delay and escalated (7) or withheld (2)        |

So a pass is a run where somebody checked the arrival time against the deadline.

### Why the failures failed

- **88 of the 123 runs** have `LATE_LOT`: Supplier C's lot arrived after 17:00
  on November 18. This is the main failure. It usually means Supplier C stayed
  on standard transport.
- **9 runs** have `INVENTED_CAPACITY`. In these the Buyer wrote the transport
  option in its own words (for example the carrier's name instead of "standard"),
  and the checker could not match it to a real option. These are partly a
  wording artifact, not always a true invention. These counts were graded
  before two later changes: the record builder learned the words real runs
  use ("delivery", "transit", "only", "optional" and a few more), and a name
  the checker still cannot match is now `INVALID` with `UNKNOWN_OPTION`
  instead of `INVENTED_CAPACITY` (decisions N38). Regraded now, fewer runs
  carry this code and some would be `INVALID`.
- **1 run** is `FALSE_WITHHOLD` (`explicit`): the group withheld although a good
  plan existed.
- **1 run** is `QUANTITY_MISMATCH` (`disruption`).

### A closer look at `disruption`

The `disruption` case is meant to show a **stale approval**: version 1 was right,
a delay arrives, and the group re-confirms the old plan. The data shows that this
is only part of what happens. Of the 21 silent failures in the folder:

| What happened                                                                                 | Runs |
| --------------------------------------------------------------------------------------------- | ---- |
| Version 1 already had Supplier C on standard transport, so the plan was late before the delay | 15   |
| Version 1 had Supplier C on expedited (right), and the plan sent after the delay was wrong    | 6    |

So most `disruption` failures are the older late-lot failure with a delay on
top, not a clean stale approval. (Some of the 6 are also wording artifacts, as
described above.)

### How long a run takes

|                  | Value                                                 |
| ---------------- | ----------------------------------------------------- |
| Time per run     | median 28 s, from 13 s to 121 s                       |
| Messages per run | median 23, from 15 to 77                              |
| Rounds           | most runs finish in 1 to 3 rounds; the longest took 7 |

## Things to keep in mind

- **A rate, not a promise.** Thirty runs per case is still a small sample. The
  same case gave different counts on different days (for example `explicit` was
  24 of 30 on 2026-10-28, per the decisions page, and 19 of 30 on 2026-10-30).
  Read the numbers as "roughly two thirds to nine tenths", not as exact values.
- **Baseline only.** No L9 run exists yet. These results show what happens
  without ACCORD and CONCORD. Whether they prevent the failure is still open.
- **The scenario was tuned on purpose.** Prompts and data were refined on
  baseline runs until the failure appeared (for example the 60-hour transit that
  makes Supplier C only four hours late). The history of each change, with
  counts before and after, is in the
  [decisions page](supply_chain_commitment_decisions.md#n24-the-baseline-failure-is-the-aim-scenarios-are-refined-until-it-happens-your-decision-2026-10-27).
- **Run folders are local.** `runs/` is ignored by git, so these figures are a
  snapshot from one development machine, not something stored in the repository.
- **Dates in the plan text can be wrong.** The Buyer sometimes writes the year 2023. The checker ignores it and recomputes from the scenario data, so the
  verdict is not affected.
