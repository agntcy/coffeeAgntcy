# Spec Delta

## Purpose

Defines the Lungo Supply Chain Commitment workflow. Five LLM agents from
separate organizations negotiate a coffee shipment commitment in one SLIM
group, under a plain or an L9-structured configuration. A deterministic
checker grades the resulting commitment record, so we can observe whether
the predicted cognitive failures occur. The first scenario runs without
ACCORD and CONCORD to show a silent failure, in which the agents agree and
nothing looks wrong to them while the commitment is wrong. The same
scenario then runs with them to see whether they prevent it.

## ADDED Requirements

### Requirement: Five agents with separate information
The workflow SHALL run five agents: Buyer, Supplier A, Supplier B, Supplier C
and Logistics. Each agent SHALL receive only its own scenario data:
- the Buyer: quantity, grade, destination, deadline and budget;
- each supplier: its own quantity, grade and origin-ready time;
- Logistics: transport options, transit times, costs and capacity.

No agent's initial instructions SHALL contain another party's data or the
correct answer for the case.

#### Scenario: Supplier does not see transport options
- **WHEN** a run starts for any case and configuration
- **THEN** the initial instructions of Supplier A, B and C contain no transport cost, transit duration or capacity figures, and the Buyer's contain no supplier quantities or ready times

#### Scenario: Logistics does not see the buyer's budget
- **WHEN** a run starts for any case and configuration
- **THEN** the Logistics agent's initial instructions contain no buyer budget or deadline

### Requirement: Negotiation happens in one attributable group over SLIM
The agents SHALL exchange negotiation messages over the A2A SLIM transport,
as one logical negotiation group per run. The Buyer process SHALL moderate
the group: each step is delivered to its addressees in a SLIM group session,
replies go back to the moderator, and the moderator relays the public
transcript to every party. Every message SHALL identify its sender, its
addressees and its sequence number within the run.

#### Scenario: Only addressed parties reply
- **WHEN** the moderator sends a step addressed to Supplier B only
- **THEN** exactly one reply is recorded for that step, from Supplier B, and no other agent produces a message for it

#### Scenario: Every message is attributable
- **WHEN** a run completes
- **THEN** every message in the saved transcript has a sender that is one of the five agents (or the run moderator for protocol relay and injected events), a non-empty list of addressees, and a unique, increasing sequence number

### Requirement: Scenario cases come from fixtures
The workflow SHALL support four cases, defined in versioned fixture data that
matches the use case specification:
- `ambiguous`: the buyer asks for delivery "by November 18".
- `explicit`: the buyer asks for "arrival at Warehouse W" by Nov 18. The deadline time of day, 17:00 UTC, is held by the Buyer's own brief only.
- `infeasible`: no expedited capacity exists.
- `disruption`: after a commitment, Supplier C's ready time moves to Nov 17,
  09:00 UTC.

#### Scenario: Ambiguous wording
- **WHEN** a run uses case `ambiguous`
- **THEN** the Buyer's initial requirement text states the deadline as delivery by November 18 without naming the milestone

#### Scenario: Disruption is injected after commitment
- **WHEN** a run uses case `disruption` and the first negotiation ends with a commitment
- **THEN** Supplier C is told its ready time changed to Nov 17, 09:00 UTC, the group is told the plan may be affected, and negotiation continues on a new plan version

#### Scenario: Disruption without a first commitment
- **WHEN** a run uses case `disruption` and the first negotiation ends without a commitment
- **THEN** no disruption is injected and the run ends with that outcome

### Requirement: Negotiation configuration is selectable per run
Each run SHALL use exactly one configuration: `baseline`, `l9_hybrid` or
`l9_full`. The same role instructions, fixtures and model SHALL be used in
every configuration. `l9_full` SHALL be rejected with a clear "not
implemented" message until it is implemented.

#### Scenario: Selecting a configuration through the API
- **WHEN** a client starts a run with configuration `baseline` and case `explicit`
- **THEN** the run uses the plain negotiation without any L9 protocol messages

#### Scenario: Selecting a configuration through a prompt
- **WHEN** a user sends a chat prompt naming a case and a configuration (for example, "run the infeasible case with L9")
- **THEN** the run uses that case and configuration, and the first streamed event states which case and configuration were chosen

#### Scenario: Selecting a configuration through the closing tag
- **WHEN** a prompt ends with a tag `(<case>/<run type>)`, for example `(ambiguous/L9 hybrid)`, and the request has no `case` or `configuration` field
- **THEN** the run uses the tagged case and configuration without reading the prompt with a model, and the first streamed event states them

#### Scenario: Explicit fields win over the tag
- **WHEN** a request has `configuration` `baseline` and its prompt ends with the tag `(ambiguous/L9 hybrid)`
- **THEN** the run uses `baseline`

#### Scenario: Unimplemented configuration
- **WHEN** a client starts a run with configuration `l9_full`
- **THEN** no agent is contacted and the response states that `l9_full` is not implemented yet

### Requirement: Suggested prompts name the goal and the run type
The chat SHALL offer suggested prompts written as requests a person would
give, one for each of the four assumed failures (`DR-1`, `CE-1`, `IE-1`,
`CC-4`) and each run type, each ending in a tag `(<case>/<run type>)` with
the run type written `baseline`, `L9 hybrid` or `L9 full`. The offered list
SHALL follow `SUPPLY_CHAIN_L9_ENABLED`: when L9 is off no offered prompt
SHALL name an L9 run type.

#### Scenario: L9 is on
- **WHEN** `SUPPLY_CHAIN_L9_ENABLED` is on and a client asks for the suggested prompts
- **THEN** the response has 12 prompts, grouped by goal, and each prompt's tag equals the case and configuration it stands for

#### Scenario: L9 is off
- **WHEN** `SUPPLY_CHAIN_L9_ENABLED` is off and a client asks for the suggested prompts
- **THEN** the response has 4 prompts, all with the run type `baseline`, and none mentions L9

#### Scenario: An L9 prompt sets the configuration
- **WHEN** a user chooses the suggested prompt ending in `(ambiguous/L9 hybrid)`
- **THEN** the run uses case `ambiguous` and configuration `l9_hybrid`

### Requirement: A baseline run contains no ACCORD or CONCORD
A `baseline` run SHALL NOT contain any ACCORD or CONCORD message, and no
skill text or protocol tool SHALL reach any agent's model. A deployment
switch, `SUPPLY_CHAIN_L9_ENABLED` (default off), SHALL be able to disable L9
for every agent. Each run SHALL record whether L9 was available to it.

#### Scenario: Baseline run has no L9 content
- **WHEN** a `baseline` run completes
- **THEN** no transcript message has an `accord_*` or `concord_*` kind, no agent prompt contains skill text, and no protocol tool was bound to a model

#### Scenario: Switching L9 off
- **WHEN** `SUPPLY_CHAIN_L9_ENABLED` is off and a client starts a run with configuration `l9_hybrid`
- **THEN** no agent is contacted and the response states that L9 is disabled in this deployment

#### Scenario: L9 messages reach an agent while L9 is off
- **WHEN** `SUPPLY_CHAIN_L9_ENABLED` is off and an agent receives an `accord_request` or `concord_request`
- **THEN** the agent replies with an error without reading the skills directory or calling its model

#### Scenario: Both configurations in one deployment
- **WHEN** `SUPPLY_CHAIN_L9_ENABLED` is on and two runs of the same case use `baseline` and then `l9_hybrid`
- **THEN** both run on the same deployed agents without a restart, and each run's saved metadata names its configuration and states that L9 was available

### Requirement: L9 hybrid runs ACCORD before CONCORD with the vendored scripts
In `l9_hybrid`, the run SHALL complete ACCORD (convene, two frame rounds,
ground, clarify when the script requests it, verify and execution) before
CONCORD starts.

Every merge and every decision SHALL be computed by the vendored initiator
scripts. Every protocol message an initiator script prints SHALL be
delivered to its addressees unchanged.

The protocol content SHALL come from the agents' LLMs. This covers atoms,
term definitions, checks, anchors, candidates, scores and repairs, and the
initiator choices of key terms, required knowledge, objective clauses,
candidate schema and anchors. The run's code SHALL NOT supply any of it.

#### Scenario: Protocol order
- **WHEN** an `l9_hybrid` run completes
- **THEN** its transcript shows the ACCORD phases in order, a locked intent contract with status `COMPLETE` or `FLAGGED`, then the CONCORD anchor, seed, score and any repair rounds, and finally a commit with outcome `SUCCESS` or `BEST_EFFORT`

#### Scenario: Key terms are not handed to the agents
- **WHEN** an `l9_hybrid` run initializes ACCORD
- **THEN** the key terms passed to the initiator script are the ones the Buyer's LLM chose, and the run records whether "delivery" (or a synonym) was among them

#### Scenario: ACCORD replies are independent
- **WHEN** an agent answers an ACCORD convene, frame, ground, clarify or verify request
- **THEN** its prompt contains no other agent's reply to the same phase

#### Scenario: Script error stops the run
- **WHEN** an initiator script exits with an error or returns `ok: false`
- **THEN** the run stops, streams the script error, records the outcome as `protocol_error`, and does not produce a committed record

### Requirement: Every run produces a structured commitment record
Every run SHALL end with a commitment record containing these fields:
- run id, case, configuration and plan version;
- status: `committed`, `withheld` or `escalated`;
- per supplier: tonnes, grade, origin-ready time, transport option and
  claimed arrival time at the destination;
- destination, arrival deadline, total transport cost and the
  delivery-milestone definition used;
- the confirmation of each of the five parties for that plan version;
- references to the message sequence numbers that support each field.

A party's confirmation SHALL count only if that party sent it for the
recorded plan version.

#### Scenario: Committed record lists confirmations
- **WHEN** a run ends with status `committed`
- **THEN** the record contains one confirmation entry per party, each naming the plan version and the sequence number of the confirming message

#### Scenario: Old approvals do not carry over
- **WHEN** a `disruption` run produces plan version 2
- **THEN** version 1 confirmations are not counted toward version 2

### Requirement: Deterministic checker grades every run
After every run, a deterministic program (not an agent) SHALL evaluate the
commitment record against the case fixtures. It SHALL recompute the arrival
times and costs from the fixtures instead of trusting the record's claimed
values. Its output SHALL never be sent to any agent.

The checker SHALL run in the background of the run, after the run ends. Its
verdict and the record SHALL be streamed to the feed and saved, and the
checker SHALL NOT appear as a node in the workflow graph.

The verdict SHALL grade the outcome against the fixtures, never the
communication process. It SHALL be `PASS`, `FAIL` or `INVALID`. `INVALID`
SHALL be used when the run ended because of a `timeout` or a
`protocol_error`, and SHALL carry no failure codes, so that an outage is not
counted as a cognitive failure. Runs without a verdict (cancelled runs) and
`INVALID` runs SHALL be counted separately in summaries, never as `PASS` or
`FAIL`.

A `PASS` or `FAIL` verdict SHALL carry zero or more failure codes:
- `FALSE_COMMITMENT`, `FALSE_WITHHOLD`;
- `LATE_LOT`, `OVER_BUDGET`, `QUANTITY_MISMATCH`, `GRADE_MISMATCH`;
- `INVENTED_CAPACITY`, `STALE_PLAN`;
- `MISSING_CONFIRMATION`, `VERSION_MISMATCH`, `MILESTONE_UNRESOLVED`.

#### Scenario: Feasible case committed correctly
- **WHEN** an `ambiguous` or `explicit` run commits 400, 350 and 250 tonnes, with expedited transport for Supplier C, arrival Nov 18, 09:00 UTC and cost $19,000, confirmed by all five parties for the same version
- **THEN** the verdict is `PASS`

#### Scenario: All-standard plan committed
- **WHEN** a run commits a plan in which Supplier C ships by standard transport
- **THEN** the verdict is `FAIL` with `LATE_LOT` and `FALSE_COMMITMENT`

#### Scenario: Infeasible case committed
- **WHEN** an `infeasible` run ends with status `committed`
- **THEN** the verdict is `FAIL` with `FALSE_COMMITMENT`, and `INVENTED_CAPACITY` if the record uses expedited transport

#### Scenario: Infeasible case withheld
- **WHEN** an `infeasible` run ends with status `withheld` or `escalated`
- **THEN** the verdict is `PASS`

#### Scenario: Feasible case withheld
- **WHEN** an `ambiguous` or `explicit` run ends with status `withheld` or `escalated`
- **THEN** the verdict is `FAIL` with `FALSE_WITHHOLD`

#### Scenario: Disruption ignored
- **WHEN** a `disruption` run ends with the version 1 plan still `committed`
- **THEN** the verdict is `FAIL` with `STALE_PLAN`

#### Scenario: Clean process, wrong result
- **WHEN** every step of a run got its replies, all five parties confirmed the same plan version, and the plan ships Supplier C by standard transport
- **THEN** the verdict is `FAIL` with `LATE_LOT` and `FALSE_COMMITMENT`, even though the process had no error

#### Scenario: Outage is not a cognitive failure
- **WHEN** an `ambiguous` run ends with status `withheld` and reason `timeout` or `protocol_error`
- **THEN** the verdict is `INVALID` with no failure codes, and not `FAIL` with `FALSE_WITHHOLD`

#### Scenario: Round limit is graded
- **WHEN** an `ambiguous` run ends with status `withheld` and reason `round_limit`
- **THEN** the verdict is `FAIL` with `FALSE_WITHHOLD`

#### Scenario: Checker sends nothing to agents
- **WHEN** any run completes
- **THEN** no message in the transcript after the checker ran is addressed to an agent

### Requirement: Silent failures are identified
Each graded run SHALL carry a `silent` flag. The flag SHALL be true only
when all of these hold: the status is `committed`; each of the five parties
sent one `confirm` for the recorded plan version; no reply anywhere in the
run was a rejection and nothing was escalated; and the verdict is `FAIL`.
The flag SHALL be computed from the verdict, the record and the run signals,
not from message text, and SHALL be included in the streamed verdict and the
saved run files. A run summary SHALL report, per case and configuration, the
numbers of silent failures, other failures, passes and invalid runs.

#### Scenario: Everyone agrees and the plan is late
- **WHEN** an `ambiguous` run commits an all-standard plan and all five parties confirm it without any rejection
- **THEN** the verdict is `FAIL` and the `silent` flag is true

#### Scenario: A party objected along the way
- **WHEN** an `ambiguous` run commits a late plan after Logistics rejected an earlier version
- **THEN** the verdict is `FAIL` and the `silent` flag is false

#### Scenario: Correct commitment is not silent
- **WHEN** a run ends with verdict `PASS`
- **THEN** the `silent` flag is false

#### Scenario: Invalid run is not silent
- **WHEN** a run ends with verdict `INVALID`
- **THEN** the `silent` flag is false

### Requirement: Runs are streamed and saved
The Buyer's chat API SHALL stream every negotiation message, the commitment
record and the checker verdict as NDJSON lines with valid JSON content. Each
run's transcript, record, verdict and L9 script state SHALL be saved as files
in a run directory that is excluded from version control.

#### Scenario: Message text with apostrophes
- **WHEN** an agent's message contains an apostrophe or a double quote
- **THEN** the streamed line parses as JSON and the feed shows the text unchanged

#### Scenario: Run files saved
- **WHEN** a run completes, fails or times out
- **THEN** its run directory contains the transcript and the outcome, and the record and verdict when they were produced

### Requirement: Run limits are bounded and reported
Each run SHALL have configurable limits: a maximum number of baseline rounds,
the CONCORD satisfaction threshold and budget, and an overall timeout.
Reaching a limit SHALL end the run with an explicit outcome, never with a
silent commitment.

#### Scenario: Baseline round limit reached
- **WHEN** a baseline run reaches its maximum number of rounds without a Buyer decision
- **THEN** the run ends with status `withheld` and reason `round_limit`, and the checker grades it

#### Scenario: Overall timeout reached
- **WHEN** a run reaches its overall timeout
- **THEN** the run ends with status `withheld` and reason `timeout`, and the checker marks it `INVALID`

### Requirement: Catalog entry and graph
The Agentic Workflows catalog SHALL list a workflow named "Supply Chain
Commitment" with these fields:
- pattern `Secure Group Collaboration`;
- category "Multi-Agent Communication & Collaboration";
- use case "Coffee Agntcy" and scenario "Supply Chain Commitment";
- chat API target `supply_chain`.

Its topology SHALL contain one group node holding the Buyer, Supplier A,
Supplier B, Supplier C, Logistics and an A2A SLIM transport node. It SHALL
NOT contain a checker node or a record node.

#### Scenario: Graph contents
- **WHEN** the UI opens the Supply Chain Commitment workflow
- **THEN** the graph shows the negotiation group with the five agent nodes and the SLIM transport, and no checker node

#### Scenario: Feed highlights the sender
- **WHEN** a streamed negotiation message arrives from Supplier B
- **THEN** the Supplier B node is highlighted in the graph
