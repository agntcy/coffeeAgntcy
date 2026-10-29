# Supply Chain Commitment: Run Types and Suggested Prompts

This page explains two things: how the three run types differ, and which
suggested prompts test which goal. It belongs to the OpenSpec change
`add-supply-chain-commitment-use-case`. Design decisions are in
[supply_chain_commitment_decisions.md](supply_chain_commitment_decisions.md).

Status: the baseline prompts below are built and the cases behind them are
being refined (decisions N25 to N27, latest results there). The L9 run types
are planned. See [What is built today](#what-is-built-today) for the gap.

## 1. The three run types

A run type is the `configuration` of one run. All three use the same agents,
role prompts, scenario data, model, confirm round, commitment record and
checker. Only the way the group negotiates differs.

| Aspect | `baseline` | `l9_hybrid` | `l9_full` |
|---|---|---|---|
| Name in a prompt | baseline | L9 hybrid | L9 full |
| One-line idea | Plain group negotiation in natural language | The same negotiation, structured by ACCORD then CONCORD | The same, but each agent drives the L9 skills itself |
| Who runs ACCORD and CONCORD | Nobody | The Buyer's code runs the vendored initiator scripts. Each agent's LLM only answers as a receiver | Each agent's LLM holds its own skill text and calls the scripts and delegation tools itself |
| Message kinds on the wire | `negotiation`, `confirm_*`, `event` | Those plus `accord_*` and `concord_*` | Not designed yet |
| Skill text in any prompt | None | The receiver skill text, only for the matching L9 message | The full skill text of every agent |
| Protocol tool for the model | Never bound | `concord_forge`, only while answering an L9 message | Initiator and delegation tools |
| How "delivery" is settled | Each role keeps its own meaning. Nobody is required to ask | ACCORD aligns scope, glossary and acceptance checks first. Upstream CLARIFY returns an empty ambiguity list, so a flagged term stays flagged | Left to the agents, not designed yet |
| How a plan comes about | The Buyer's LLM decides each round: continue, propose a plan, withhold or escalate | CONCORD converges on one plan under a locked contract. The Buyer's LLM then proposes, withholds or escalates | Not designed yet |
| How a plan is committed | The confirm round: all five parties confirm the same plan version | The same confirm round | The same confirm round |
| LLM calls per run | Fewest (about 20 to 40 in the first probe) | More, because of the protocol phases | Most |
| Needs `SUPPLY_CHAIN_L9_ENABLED` on | No, works either way | Yes | Yes |
| Offered as a suggested prompt | Always | Only when L9 is on | Only when L9 is on |
| Role in the demo | Shows the failure, and that it can be silent | Tests whether the protocols prevent it (a hypothesis, not a promise) | Later comparison |
| Status | Built (task 4.3) | Planned (tasks 4.4 and 4.5) | Declared only. The Buyer answers "not implemented" (task 4.8) |

**Summary.** `baseline` is the control: nothing structures the negotiation, so
whatever the agents get wrong stays unchallenged. `l9_hybrid` adds ACCORD
(shared meaning) and CONCORD (shared plan) around the same negotiation, run
by the Buyer's code so that every message follows the protocol word for word.
`l9_full` is the same idea with the agents in charge of the protocol. It is
reserved so it can be added later without reworking the other two. The
baseline failure is the aim: a case is refined until the baseline fails
silently, and only then is it run with `l9_hybrid`. Whether `l9_hybrid`
prevents that failure is the real test, and "it does not" is a valid finding.

## 2. The goals and their prompts

The goals are the four cognitive failures the use case assumes (see the
[proposal](../../../../openspec/changes/add-supply-chain-commitment-use-case/proposal.md)).
They are only assumptions until a run shows them, so each case is first
tried on `baseline`. Where the agents handle a case correctly, the case is
refined (more realistic or more demanding, one change at a time, logged)
until the baseline fails silently. That failing version is then frozen and is
the one that runs with ACCORD and CONCORD, because only a failure that
really happens can show what the protocols are worth. The example prompts
below describe the cases as they are today and are updated with each
refinement.

| Goal | What to test | Case | A failure looks like | Example prompt (baseline) |
|---|---|---|---|---|
| `DR-1` Different meanings of "delivery" | Do the parties agree on one milestone when the buyer says "delivered by November 18" without naming it? | `ambiguous` | All five confirm a plan that is late at Warehouse W (a silent failure) | I'd like to have a 1,000-tonne coffee shipment delivered by November 18, with total transport cost at or below $20,000 (ambiguous/baseline) |
| `CE-1` Commitment without a feasibility check | With the milestone stated clearly, does the group still check each lot's arrival before it commits? | `explicit` | The group commits the plan with Supplier C on standard transport, which arrives 4 hours after the 17:00 deadline | I'd like to have a 1,000-tonne coffee shipment arrive at Warehouse W by November 18, with total transport cost at or below $20,000 (explicit/baseline) |
| `IE-1` Invented capacity | When expedited transport has no capacity, does the group say so, or invent capacity or relax the deadline? | `infeasible` | The group commits a plan although no transport option meets the deadline (Supplier C on standard arrives late) | I'd like to have a 1,000-tonne coffee shipment arrive at Warehouse W by November 18, with total transport cost at or below $20,000, with expedited transport unavailable (infeasible/baseline) |
| `CC-4` Stale approval carried forward | After a commitment, when one supplier's ready time moves a day, is the plan reopened, or is the old approval reused? | `disruption` | The group confirms a plan that Supplier C's delay has made late: the old plan again, or a repaired one that ignores the new ready time | I'd like to have a 1,000-tonne coffee shipment arrive at Warehouse W by November 18, with total transport cost at or below $20,000, with one supplier reporting a one-day delay after we agree (disruption/baseline) |

`explicit` is also the contrast for `DR-1`: it is the same request with the
milestone named. The deadline's time of day (17:00 UTC) is in the Buyer's own
brief only in `explicit`, `infeasible` and `disruption`, as in `ambiguous`;
with the exact time in the opening words every party held it and the
baseline passed (decisions N27). The mapping of `CE-1` to `explicit` is our reading of the
use case, which ties `CE-1` to the false commitment rate rather than to one
case.

**Summary.** Each goal has one case, and each case is offered in every run
type that is available. The headline pair is `ambiguous` with `baseline`
against `ambiguous` with `L9 hybrid`. The prompt describes the request for
a person to read. The agents' opening request always comes from the case's
fixed wording, so every run type of a case starts from the same text.

### The full prompt list

Each prompt is the baseline prompt with another run type in the closing tag.
The tag is what sets the case and the configuration.

| Goal | Run type | Prompt | Shown when |
|---|---|---|---|
| `DR-1` | baseline | I'd like to have a 1,000-tonne coffee shipment delivered by November 18, with total transport cost at or below $20,000 (ambiguous/baseline) | Always |
| `DR-1` | L9 hybrid | I'd like to have a 1,000-tonne coffee shipment delivered by November 18, with total transport cost at or below $20,000 (ambiguous/L9 hybrid) | L9 on |
| `DR-1` | L9 full | I'd like to have a 1,000-tonne coffee shipment delivered by November 18, with total transport cost at or below $20,000 (ambiguous/L9 full) | L9 on |
| `CE-1` | baseline | I'd like to have a 1,000-tonne coffee shipment arrive at Warehouse W by November 18, with total transport cost at or below $20,000 (explicit/baseline) | Always |
| `CE-1` | L9 hybrid | I'd like to have a 1,000-tonne coffee shipment arrive at Warehouse W by November 18, with total transport cost at or below $20,000 (explicit/L9 hybrid) | L9 on |
| `CE-1` | L9 full | I'd like to have a 1,000-tonne coffee shipment arrive at Warehouse W by November 18, with total transport cost at or below $20,000 (explicit/L9 full) | L9 on |
| `IE-1` | baseline | I'd like to have a 1,000-tonne coffee shipment arrive at Warehouse W by November 18, with total transport cost at or below $20,000, with expedited transport unavailable (infeasible/baseline) | Always |
| `IE-1` | L9 hybrid | I'd like to have a 1,000-tonne coffee shipment arrive at Warehouse W by November 18, with total transport cost at or below $20,000, with expedited transport unavailable (infeasible/L9 hybrid) | L9 on |
| `IE-1` | L9 full | I'd like to have a 1,000-tonne coffee shipment arrive at Warehouse W by November 18, with total transport cost at or below $20,000, with expedited transport unavailable (infeasible/L9 full) | L9 on |
| `CC-4` | baseline | I'd like to have a 1,000-tonne coffee shipment arrive at Warehouse W by November 18, with total transport cost at or below $20,000, with one supplier reporting a one-day delay after we agree (disruption/baseline) | Always |
| `CC-4` | L9 hybrid | I'd like to have a 1,000-tonne coffee shipment arrive at Warehouse W by November 18, with total transport cost at or below $20,000, with one supplier reporting a one-day delay after we agree (disruption/L9 hybrid) | L9 on |
| `CC-4` | L9 full | I'd like to have a 1,000-tonne coffee shipment arrive at Warehouse W by November 18, with total transport cost at or below $20,000, with one supplier reporting a one-day delay after we agree (disruption/L9 full) | L9 on |

## 3. How a prompt picks the run

**The closing tag.** The text in the last parentheses, `(<case>/<run type>)`,
sets the case and the configuration. Run types are written `baseline`,
`L9 hybrid` or `L9 full`. The identifiers `l9_hybrid` and `l9_full` are
accepted too, in any letter case. The plan reads the tag with a fixed rule,
not with a model, so the same prompt always picks the same run.

**Precedence, highest first:**

1. The `case` and `configuration` fields of an API request.
2. The closing tag of the prompt.
3. A model that reads the prompt, for a prompt typed without a tag.
4. The defaults, `ambiguous` and `baseline`. The first streamed event says
   when a default was used.

**The L9 switch.** `SUPPLY_CHAIN_L9_ENABLED` decides which prompts the chat
offers. The tag then sets the configuration of the chosen run.

| `SUPPLY_CHAIN_L9_ENABLED` | Suggested prompts offered | A prompt with an L9 tag, typed by hand |
|---|---|---|
| Off (default) | 4, all `baseline`. No prompt mentions L9 | Refused: no agent is contacted, and the first events say L9 is disabled in this deployment |
| On | 12: each goal in `baseline`, `L9 hybrid` and `L9 full` | Runs with that configuration. `L9 full` answers "not implemented" until it is built |

**Summary.** With L9 off, a person using the suggested prompts cannot reach an
L9 run, so the failing demo stays free of ACCORD and CONCORD by what is on
offer, not only by what is refused. With L9 on, the choice of prompt is the
choice of run type, so the paired demo needs no restart and no setting
change.

## What is built today

- Built: the `baseline` run type (including the disruption flow, task 4.6
  baseline part), the L9 switch, the closing-tag rule, and
  `suggested_prompts.json` with the 12 prompts in the wording on this page,
  grouped by goal and filtered by the switch (4 baseline prompts while L9 is
  off). The UI shows them in one menu, labelled `SUPPLY_CHAIN` rather than by
  goal.
- Planned: the `l9_hybrid` run (tasks 4.4 and 4.5). `l9_full` answers "not
  implemented" until task 4.8 and its follow-up.
- No frontend change is needed for the prompts: the chat sends the prompt
  text, and the server reads the tag.

How to run the use case is on [supply_chain_commitment.md](supply_chain_commitment.md).
