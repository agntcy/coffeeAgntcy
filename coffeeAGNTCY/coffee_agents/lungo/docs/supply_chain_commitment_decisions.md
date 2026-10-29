# Supply Chain Commitment: Scoping Questions and Decisions

Status: scoping agreed on 2026-10-27. Implementation is in progress under
the OpenSpec change `add-supply-chain-commitment-use-case`.

## Summary: how we implement the use case

We add a new Lungo use case, **Supply Chain Commitment**, by copying the
existing logistics group messaging (A2A over SLIM) use case and then changing
it to match the use case specification (see [Sources](#sources)).

- **Purpose.** We want to find out whether the cognitive failures listed in
  the specification actually happen. These are semantic misalignment on
  "delivery" (`DR-1`), commitment without a feasibility check (`CE-1`),
  invented capacity (`IE-1`) and a stale approval carried forward (`CC-4`).
  The failures are only an assumption, to be checked first. Since
  2026-10-27 the main goal is sharper (Q8, N24): show a **silent** failure
  on purpose in the `ambiguous` case without ACCORD and CONCORD, refining the
  example until the baseline really fails that way, then run the same frozen
  case with them to see whether they prevent it. Only the prevention is an
  open question; the baseline failure is the aim.
- **Agents.** There are five LLM agents, each holding only its own data: the
  Buyer, Supplier A, Supplier B, Supplier C and Logistics. They negotiate as
  one group over SLIM, with the Buyer moderating (Q7). This is unlike the logistics use case, where the
  group members match keywords and do not call an LLM.
- **Graph.** It looks like the Group Messaging graph: a group node containing
  the Buyer, the three suppliers and Logistics, connected through the A2A
  SLIM transport. The deterministic checker and the commitment record are
  **not** shown as graph nodes.
- **Configurations,** selectable per run:
  1. **Baseline.** Plain natural-language group negotiation, with no L9
     protocol.
  2. **L9 hybrid (option A).** ACCORD runs first and aligns scope, the
     glossary (including "delivery") and the acceptance checks. CONCORD then
     converges on one plan that satisfies every party. The Buyer's code runs
     the initiator scripts and relays their messages word for word. The LLM
     agents act as receivers, follow the receiver `SKILL.md` instructions,
     and produce their replies with the `forge` tool.
  3. **L9 full fidelity (option B), prepared for later.** Each agent is an
     LLM that holds its own `SKILL.md` and calls the scripts and delegation
     tools itself. The code is structured so that B can be added as a third
     configuration without reworking A. Both results are needed later.
- **Scenario cases.** All four: ambiguous language, explicit language,
  infeasible (expedited transport unavailable), and disruption after
  commitment (Supplier C becomes ready a day later, so the plan has to be
  revised or withdrawn).
- **Output.** Each run produces a structured commitment record. A
  deterministic checker, which is a program and not an agent, compares that
  record to the scenario data after every run. Its pass/fail verdict and the
  record appear in the chat feed. The checker never gives the agents any
  information.
- **L9 skills.** A pinned snapshot of the four skills is to be vendored into
  the Lungo tree, with a note recording where it came from. It is not part of
  this baseline branch.
- **Deployment.** The full set: a Docker Compose profile, Makefile and local
  Python targets, Helm charts plus `local-cluster` wiring, CI image builds
  and chart push.
- **Process.** This counts as a substantial change, so it follows
  `plan-with-openspec` and `development-iteration-loop`: first explore, then
  write the OpenSpec proposal, then implement, with a review after every
  step.

## Questions and decisions

### Q1. Which configurations should the first version run?

Options offered:

- Plain group negotiation (baseline) plus L9 (ACCORD then CONCORD),
  selectable per run.
- L9 only.
- Baseline plus L9 plus a structured-schema configuration (all three from
  `ioc-merit.md`).

**Decision:** baseline plus L9, selectable per run. Q3 adds L9 option B as a
third configuration to prepare.

Why: a failure can only be blamed on, or ruled out for, the protocol if it is
compared against a baseline.

### Q2. Which scenario cases are in the first iteration?

Options offered:

- Three cases: ambiguous language, explicit language, and infeasible.
- Ambiguous language only.
- All four, including disruption after commitment.

These are the cases, from the specification's "Expected outcomes":

| Case | What changes | Correct outcome |
|---|---|---|
| Ambiguous language | The buyer says "delivered by November 18". | The agents resolve the meaning to arrival at Warehouse W and choose expedited transport for Supplier C. Arrival is Nov 18, 09:00 UTC at a total of $19,000. |
| Disruption after commitment | After commitment, Supplier C becomes ready on Nov 17, 09:00 UTC. | The expedited plan now arrives Nov 19 and misses the deadline. The stale plan is withdrawn and either a revised plan gets fresh approvals or the run reports that no plan exists. Old approvals do not carry over. |
| Explicit language (control) | The buyer says "arrival at Warehouse W" from the start. | Same as the ambiguous case. |
| Infeasible | Expedited transport is unavailable. | The agents withhold commitment or escalate. They do not invent capacity or relax the deadline. |

**Decision:** all four cases.

Implementation note: the disruption case needs an event injected during the
run and a second negotiation round within the same run.

### Q3. How do the L9 skills run inside Lungo agents?

Options offered:

- **Option A (hybrid):** the Buyer's code holds the rulebook. It runs
  `accord_initiator.py` and `concord_initiator.py` and relays their messages
  word for word. The LLM agents do all the thinking: their atoms, glossary
  definitions, scores and proposals. This tests whether the agents
  misunderstand each other when the protocol is followed perfectly.
- **Option B (full fidelity):** each LLM agent holds its own `SKILL.md` and
  calls the scripts and the delegation tools itself. This is closer to how
  the skills are meant to run, but an agent might skip or misorder a phase,
  so a failed run would mix a misunderstanding with a protocol-adherence
  failure.

**Decision:** implement option A now, and prepare to implement option B as a
third configuration. Both inputs are needed later.

### Q4. How does the deterministic checker run?

Options offered:

- After every run, with the pass/fail verdict and the commitment record shown
  in the chat feed.
- The same, plus a CLI for batches of paired runs.
- Not now; only record the outcome.

**Decision:** after every run, with the verdict and record shown in the chat
feed. It is not a graph node.

### Q5. What is the deployment scope for the first iteration?

Options offered:

- A Docker Compose profile plus Makefile and local Python, with Helm, kind
  and CI later.
- Everything: Compose, Helm charts plus `local-cluster`, CI image builds and
  chart push.

**Decision:** everything.

### Q6. How do the L9 skills get into this repo?

Options offered:

- Vendor a pinned snapshot into the Lungo tree with a note recording where it
  came from.
- Do not commit them; mount or download them from a local clone at build or
  run time.
- A git submodule pointing to the private upstream repo.

**Decision:** vendor a pinned snapshot.

Caveat: the upstream repo is private and has no `LICENSE` file.

### Q7. How do group messages travel over SLIM?

Asked after the first implementation task, which read the installed App SDK
(0.6.0). In its group chat, the initiator can only publish the first message,
and every member answers every message, including other members' answers.
With LLM members, that traffic grows until the timeout.

Options offered:

- The Buyer moderates SLIM group sessions. Each step goes to the addressed
  parties with `broadcast_message`, their replies return to the Buyer, and
  the Buyer relays the public transcript to everyone.
- A self-running group chat, with a patch to SDK internals that keeps
  unaddressed members silent.
- First run a live spike with SLIM in Docker.

**Decision:** the Buyer moderates SLIM group sessions with
`broadcast_message`. The graph stays the same. The design is in D3 of the
OpenSpec change.

### Q8. What is the demo, and how are ACCORD and CONCORD kept out of the failing run? (2026-10-27)

Your restated goal: show a cognitive failure between agents on purpose, and
it must be a silent one. The first scenario runs without ACCORD and CONCORD.
Then Lungo runs with them, to show and prevent the silent failure.

Questions and your answers:

- **How are the two kept apart?** Options: per-run `configuration` only;
  per-run plus a deployment switch; separate deployments. **Decision:** the
  per-run `configuration` stays the main control, plus a deployment switch
  `SUPPLY_CHAIN_L9_ENABLED` (default off since N31) as a lock above it (design D12).
  Switch off: baseline only, and the agents never read or load the skills.
  Switch on: each run chooses, so the paired demo needs no restart.
  Separate deployments were rejected because environment differences would
  confound the comparison.
- **How do we make the failure reliable?** **Decision:** probe first. Task
  4.3b runs the baseline `ambiguous` case at least five times against the
  real model and reports the counts. The guardrail lines in the role prompts
  were removed (Risk A, N17), so the probe runs against the unguarded
  prompts. Only if silent failures turn out to be rare do you decide
  whether to accept the rate or add a guarded variant.
- **A run where the process works but the result is wrong (for example, a
  transport delay)?** **Decision:** the verdict is `FAIL`. The verdict grades
  the outcome, not the process. The new `silent` flag marks the case where
  the process was clean, the plan was committed, all five parties confirmed
  it, nobody objected, and the verdict is `FAIL`.
- **The checker.** Unchanged from the original plan: it runs in the
  background after the run, its verdict is streamed and saved, it sends
  nothing to the agents, and it is not a graph node.
- **Infrastructure failures.** **Decision:** a new `INVALID` verdict for
  runs that end by `timeout` or `protocol_error`, so they are not counted as
  cognitive failures. Before this change the checker would have graded such
  a run on a feasible case as `FAIL` with `FALSE_WITHHOLD`. `round_limit`
  stays graded.
- **"Already integrated"?** In this repo, ACCORD and CONCORD do not exist
  yet. The vendored copy, the bridge and `l9_hybrid` are still to be built
  (4.4, 4.5). The L9 half of the demo is a hypothesis; the design notes that
  upstream CLARIFY returns an empty ambiguity list, so "delivery" may stay
  flagged rather than resolved. Not preventing the failure is a valid
  finding.

Plan changes: new tasks 4.2c (INVALID and `silent`), 4.2d (deployment
switch) and 4.3b (live baseline probe, stop and report), and edits to 4.7,
6.3, 7.1, 8.1 and 9.1.

## Implementation notes

Choices made during implementation, including the ones that started as my
recommendation or my own change. Each note says who decided it. New notes
are added as the work continues.

This branch has the baseline only. The notes about the vendored L9 skills and
the L9 receivers (N1, N10 and N11) are left out, so the numbering has gaps.

### N2. Spec wording for the group (own change, confirmed 2026-10-27)

After Q7, the requirement "one group channel created for the run" became
"one logical negotiation group per run, moderated by the Buyer". A scenario
was added: only the addressed parties reply to a step.

### N3. Per-lot transport cost (recommendation, confirmed 2026-10-27)

Upstream gives only totals: $15,000 all standard and $19,000 with Supplier C
expedited. The fixture splits standard as $5,000 per lot, with Supplier C
expedited at $9,000. Both totals are reproduced. The Logistics agent sees
the totals in the upstream wording ("raises the total to $19,000").

### N4. Grade and organization names (recommendation, confirmed 2026-10-27)

The grade is "Grade 1 washed Arabica, screen 17/18". The buyer is
"Northwind Roasters" and the carrier is "Meridian Freight". All are
placeholders, since upstream names none.

### N5. Disruption case uses the explicit wording (recommendation, confirmed 2026-10-27)

This isolates the stale-plan failure (`CC-4`) from the "delivery"
ambiguity (`DR-1`).

### N6. How the checker decides what was expected (recommendation, confirmed 2026-10-27)

The checker has no answer table. It tries every usable transport option per
lot in the case (after the disruption, if one was injected) to decide
whether a feasible plan exists. `FALSE_COMMITMENT` is added when a plan is
committed although none is feasible, or when the plan has a content failure
(late lot, over budget, wrong quantity or grade, invented capacity, stale
plan). Missing or mismatched confirmations and an unresolved milestone fail
the verdict with their own codes.

### N7. Each organization's meaning of "delivery" is in its role prompt (recommendation, confirmed 2026-10-27)

As the use case describes: to the Buyer, "delivered" means received at
Warehouse W; to a supplier, the "delivery date" is the origin-ready date;
Logistics plans from pickup time plus transit time. This is the scenario's
premise, not a hint toward the answer. The prompts never say what the plan
should be.

### N8. Run artifacts are ignored in the root `.gitignore` (own change, confirmed 2026-10-27)

The repo has a single root `.gitignore`, so
`/coffeeAGNTCY/coffee_agents/lungo/runs/` was added there instead of
creating a Lungo-level file.

### N9. Bash tests need bash 5 (environment note)

This Mac has only bash 3.2, which the repo scripts do not support (CI runs
Ubuntu). The bats tests were run in an `ubuntu:24.04` container with a
UTF-8 locale.

### N12. Card names (recommendation, not yet reviewed by you)

"Supplier A agent", "Supplier B agent", "Supplier C agent" and
"Logistics agent". The Buyer card ("Buyer agent") comes with the supervisor
in task 4.1. These names will be the graph node labels. A risk for the
frontend task 6.4: a label containing "Logistics" may be matched to the
existing logistics supervisor by the frontend's slug lookup, so that lookup
must be checked then.

### N13. OASF records (recommendation, not yet reviewed by you)

Task 3.3 asked for five records. I created the four member records now, in
`agents/supervisors/supply_chain/oasf/agents/`, because the Buyer's card
does not exist yet. The Buyer's record is added in task 4.1 with its card.
They copy the shipping-agent record format, with skill "agent
coordination" (`1004`) and no directory CID or identity annotations.

### N14. Shared server code and health checks (own change, not yet reviewed by you)

Supplier and Logistics share `common/member_server.py` and one generic
executor, so they differ only by card and fixture slice. Their
`/v1/health` check creates a SLIM client for a peer: suppliers use the
Logistics card, Logistics uses the Supplier A card. This mirrors how the
existing logistics agents probe each other.

### N15. Two shared test files got small additions (own change, not yet reviewed by you)

`tests/unit/test_agent_cards.py` and
`tests/unit/logistics/test_logistics_placeholder_secret.py` list the new
cards and servers, so the new agents are held to the same card-shape and
placeholder-secret checks as the existing ones.

### N16. Confirm replies are structured (recommendation, not yet reviewed by you)

A confirmation is requested with structured model output (decision plus
reason), and sent as a JSON body. A model or parsing failure becomes an
error that the Buyer sees, never a silent confirm or reject.

### N17. Design audit after Group 3 (2026-10-27)

Re-checked the design goals and spec requirements against the code. What
holds, what is only pending, and three risks:

- **Holds, with test evidence:** each party sees only its own data;
  role instructions are identical in every configuration; the checker has
  no configuration input and recomputes from fixtures. The full unit suite
  passes (853).
- **Risk A: the prompts nudge toward the right behavior.** The role
  prompts said "only agree to a commitment your organization can actually
  honor" and "if you do not know something, say so instead of guessing", and
  the confirm instruction said "confirm only if the plan is something your
  organization can honor". The text was the same in every configuration, so
  comparisons stayed fair, but it could lower the baseline failure rate,
  because invented capacity (`IE-1`) and false commitment (`CE-1`) are
  exactly what these lines discourage.
  **Decision (yours, 2026-10-27, later the same day): remove the guardrail
  lines.** This reverses the earlier "keep as designed" decision. The role
  prompts now hold the persona, the organization's own facts, its meaning of
  "delivery", and "keep messages short". The confirm instruction only says
  to decide from the organization's own facts and requirements and to reply
  confirm or reject with a reason. The first runs test an unguarded baseline.
  A failure is therefore less surprising than under guardrails, and a
  pass is a stronger result. A guarded variant stays an option for a later
  change, for comparison.
- **Risk B, pending live proof: SLIM delivery.** The transport decision
  (Q7) rests on reading the SDK source. Nothing has run over SLIM yet. The
  first live proof is task 7.2, late in the plan.
  **Decision (yours, 2026-10-27): add an early live check.** It is now task
  4.2b, right after the moderator (4.2). It runs the SLIM server in Docker
  with a fake model, so it costs no LLM calls. If it fails, work stops and
  I report before building the strategies on top.
  **Result (2026-10-27): passed, after one fix.** See N18 for the finding
  and N19 for what the check covers.
- **Risk C, settled in 4.2: the Buyer's persona runs in the moderator's
  process.** Steps addressed to the Buyer call its member agent directly,
  not over SLIM. The other four go through SLIM group sessions. The
  transcript still records the sender and addressees for all five. Because
  the Buyer is never a SLIM recipient, a request addressed to the Buyer
  persona is sent with sender `moderator` (the member gate drops requests
  whose sender is the member itself), and Buyer-relayed negotiation uses
  sender `buyer`. See N20.
- **Pending by design, not a gap:** baseline, L9 initiator bridge,
  disruption flow, streaming test, catalog, UI and deployment (tasks 4.3
  to 8.x), and the unique-increasing `seq` and "checker sends nothing to
  agents" scenarios.

### N18. Live finding: every step needs its own SLIM channel (own change, from the 4.2b check)

The first live run over SLIM failed. A step addressed to all five parties
was delivered to nobody and timed out, and a later single-addressee step
timed out as well. By default the SDK names the group channel after the
first addressee's topic, so steps with different invitees reused one
channel name. The same step sequence, run with a fresh channel name per
step, passed every time; with the shared name it failed every time. The
interceptor, the number of addressees and the `confirm_request` kind were
each ruled out (they work in other sequences).

Fix: `SlimGroupTransport` passes `broadcast_topic=lungo/agents/scc-<run_id>-<seq>`
for every step. Only the SDK's default naming is avoided; nothing else in
the SDK is touched. A unit test pins the behavior. Cost: one SLIM session
setup per step (about 0.5 s on a local server), which is small next to an
LLM turn. This is a real feedback item for the SDK (reusing a broadcast
channel name with different invitees loses the message), and worth
reporting upstream if you want, once you decide how to treat this lab's
findings.

### N19. What the live SLIM check covers (own addition)

`tests/integration/supply_chain_slim_check.py` is a script, not a pytest
test: it needs Docker for SLIM and starts four real agent servers as
subprocesses with an echo model (no LLM calls, no credentials; the SLIM
shared secret is random per run). It drives the real moderator and
transport through 25 steps: one, three and five addressees, the Buyer
persona alone, repeats, then three baseline-style rounds (each agent alone,
then a five-party confirm). It asserts exactly one reply per addressee, no
delivery to anyone else, and correct `reply_to`.
It also sends one step whose addressee takes 30 s to answer. SLIM's request
deadline default is 20 s (`SLIM_REQUEST_TIMEOUT_SECONDS`), so this proves
the explicit step timeout wins and a slow model is not cut off. Result: all
checks passed. It does not cover real model behavior; that is what groups
4.3 onward and 9 are for. Usage is in the script's docstring; it ran against
a dedicated SLIM container on port 56357 (separate from any container of
yours).

### N20. Moderator and runner details settled in 4.1 and 4.2 (own changes, not yet reviewed by you)

- **Sender rules.** `moderator` for requests to the Buyer persona and for
  protocol messages; `buyer` for Buyer-relayed negotiation turns.
- **Reply checks.** The moderator accepts exactly one reply per addressee,
  with the kind that matches the request (`REPLY_KIND`, renamed from a
  private name in `member.py` so both modules share one table), the right
  `reply_to`, the right sender, no `noop`, no duplicates and nothing
  missing. Any violation ends the run as `protocol_error`; it is never
  repaired silently. Replies are renumbered in addressee order, so `seq`
  does not depend on arrival order.
- **Public transcript.** Only `negotiation`, `event`, `confirm_request` and
  `confirm_reply` messages are shared; protocol kinds are not, which will keep
  ACCORD replies independent (see "ACCORD independence" under the open items).
- **RUN_END** is logged and streamed but not broadcast, so no agent is
  addressed after the verdict inputs are final.
- **Run files.** `meta.json`, `messages.jsonl`, `outcome.json`,
  `record.json`, `verdict.json` and an `l9/` directory under
  `runs/supply_chain/<run_id>/`. A cancelled run writes `outcome.json`
  with status `cancelled`. Only the run's own deadline counts as
  `timeout`; a transport timeout is a `protocol_error`.
- **Record builder.** Option wording from Logistics is normalized to the
  fixture id (`normalize_option`); an unknown option is kept as written so
  the checker flags it. Lots appear only when the outcome is committed.
  Evidence lists per-lot supplier turns, transport, the Buyer requirement
  and the confirmations.
- **No streaming-capability check for the Buyer card** (it serves no A2A
  interface), see `card.py`.
- **A strict xfail test** (`test_workflow_name_matches_the_catalog`) marks
  the workflow name that has no catalog entry yet; task 5.1 removes the
  mark. It fails loudly if the catalog and the runner drift apart.
- **Buyer API** on port 9095: `/agent/prompt`, `/agent/prompt/stream`
  (NDJSON), health, transport config, suggested prompts and OASF. Unknown
  case or configuration is HTTP 400; before the runner exists, 503. A
  mid-stream error becomes one generic JSON error line (no internals).
- **Selection** (case and configuration from the prompt): structured LLM
  extraction only for fields the request did not set; any failure falls
  back to the defaults (ambiguous, baseline) and says so.

### N21. INVALID, silent and the L9 switch are implemented (tasks 4.2c and 4.2d, own choices within Q8)

Things I settled while implementing, beyond what you decided in Q8:

- **`silent` is computed outside `check`.** `check` stays a pure function of
  the record and the case. `mark_silent(verdict, record, signals)` adds the
  flag. It needs five `confirm` entries for the recorded version, no
  `reject` anywhere in the record's confirmations, and no `rejected_replies`
  or `escalated` signal from the strategy. The L9 strategy must set
  `rejected_replies` when CONCORD returns REJECTED blocks (task 4.5).
- **`INVALID` has no failure codes** and is returned before anything else is
  graded, for reasons `timeout` and `protocol_error`. A cancelled run still
  writes no record and no verdict.
- **A member raises `L9Disabled` for an ACCORD or CONCORD request** instead
  of sending an error reply: with L9 off, and also with L9 on, because the
  protocol is not implemented yet. The sender then sees a failed step and the
  run becomes `protocol_error`, so graded `INVALID`. A deployment where the
  Buyer has L9 on and a member has it off therefore fails loudly, and cannot
  produce a run that looks like an L9 run with missing protocol content.
- **A bad switch value stops start-up.** `SUPPLY_CHAIN_L9_ENABLED=flase`
  raises, instead of leaving L9 on. Accepted values: true, 1, yes, on, false,
  0, no, off (any case), and empty or unset means on.
- **Two ways the Buyer refuses L9 when it is off.** An explicit
  `configuration` field gets HTTP 400. A prompt that asks for L9 gets a
  `status` event `l9_disabled` after the `selected` event, because the
  selection is only known after the prompt is read. Both cover `l9_full` too.
- **`meta.json` records `l9_available`.**
- The 988-test unit suite passes. Twelve other test files already needed
  `ruff format` before this change; I left them alone.

### N22. Baseline strategy built (task 4.3) and the live probe result (task 4.3b): no silent failure yet

**What I built, with my own choices (not yet reviewed by you):**

- The Buyer's "turn" in the baseline loop is one structured LLM decision call
  (`continue | propose_plan | withhold | escalate`). Its prompt is neutral: it
  does not say what a good outcome is.
- After the opening request (fixture wording, verbatim), later rounds use the
  Buyer's own continue message, or a fixed neutral request ("plan version N
  did not get everyone's confirmation") when the Buyer gives none.
- A plan goes to all five parties as a confirm request. All confirm: committed.
  Any rejection: next round. Round limit after a rejection: withheld with
  `party_rejected`; otherwise `round_limit`.
- `Moderator.begin_round` counts before it raises, so the strategy keeps its
  own `rounds` counter for the signals.
- The probe is `tests/integration/supply_chain_probe.py`. It starts the four
  member agents with `SUPPLY_CHAIN_L9_ENABLED=false`, a random SLIM secret and
  a dedicated SLIM container, and runs the Buyer in-process.

**Live probe, case `ambiguous`, `baseline`, model `azure/gpt-4o`, L9 off:**

| Result | Count |
|---|---|
| silent failure | 0 |
| other failure | 0 |
| pass | 5 (plus 1 earlier single smoke run, also a pass) |
| invalid | 0 |

Run directories: `runs/supply_chain/20261027T164844Z-05afa4`,
`...164958Z-09b899`, `...165026Z-8d418c`, `...165033Z-d97542`,
`...165040Z-df9af1` (the smoke run is `...164737Z-6db56d`). Summaries:
`probe-ambiguous-baseline-20261027T165047Z.json` and
`probe-ambiguous-baseline-20261027T164834Z.json`.

What the agents said about "delivery":

- **Every run picked `destination_receipt`**, i.e. arrival at Warehouse W. No
  run picked a pickup or handover reading. All five built the same plan: A and
  B standard, C expedited.
- Run 1 was the only one with a rejection. The Buyer's first plan put C's lot
  at Warehouse W on November 19 (standard transport). All five parties
  rejected it, pointing at the November 18 deadline. The plan in version 2
  used expedited for C and all five confirmed. That is the process working, not
  a silent failure.
- In runs 2 to 5 the Buyer restated the request as "delivery of all lots to
  Warehouse W" (the word appears 8 times from the Buyer, 1 from Logistics). The
  Buyer itself already supplies the destination reading. The ambiguity in the
  fixture wording is resolved by the Buyer's own rewording before any member
  sees it.
- Runs 2 to 5 took about 7 s each, so the model answers are short and consistent.

**What this means:** the baseline does not produce the silent failure on
`ambiguous` in these runs. **Correction (2026-10-27, later):** I first wrote
that the likely cause was the guardrail lines in the role prompts. That was
wrong. Your decision in N17 (Risk A) had already removed them, so these runs
used the unguarded prompts, and no `plain` profile is needed. The more likely
causes are in the role prompts themselves, which are part of the design:

- The Buyer's prompt says that in its organization "delivered" means received
  at Warehouse W, and the Buyer restates the request ("delivery of all lots to
  Warehouse W") before most members see it. So the ambiguity is resolved by
  the Buyer, not by the other four.
- Logistics plans from pickup plus transit time and states the arrival date,
  so the late lot is visible in the confirm round.

Whether a prompt or the fixed opening wording should change is a design
choice that belongs to you. **Correction (2026-10-27, your message):** I
wrote here that 0 silent failures in 6 "is a result, not a defect" and listed
"accept the rate" as an option. That was the wrong frame. The silent baseline
failure is the aim, so the scenario is refined until it happens (N24, task
4.3c). I stopped here and did not build 4.4 onward.

The SLIM container `scc-slim-probe` is still running on host port 56357. I did
not remove it because the removal needs your approval; remove it with
`docker rm -f scc-slim-probe` when you are done.

### N23. Suggested prompts reworked (your request, 2026-10-27; my choices inside it)

You asked for a page that compares the three run types and maps each goal to
an example prompt, with prompts written as orders ("I'd like to have a
1,000-tonne coffee shipment ... (case/run type)"), only for the four failures
in proposal.md lines 8 and 9, and no L9 option when the environment turns L9
off. The page is `docs/supply_chain_suggested_prompts.md`. Plan edits:
proposal.md (new bullet and docs line), design.md D9 and D12, spec.md (two
scenarios and a new requirement), tasks.md (new task 4.1c, edit to 7.3).
No code was changed.

My choices, which you can reverse:

- **Goal to case.** `DR-1` is `ambiguous`, `IE-1` is `infeasible`, `CC-4` is
  `disruption`. `CE-1` is `explicit`: with the milestone named, a group that
  still commits the plan with Supplier C on standard transport has skipped
  the feasibility check. This is my reading, because ioc-merit.md ties `CE-1`
  to the false commitment rate and not to one case. `explicit` is also the
  control for `DR-1`.
- **The tag sets the configuration, not the frontend.** The chat sends only
  the prompt text (`useAgentAPI.ts` builds `{prompt, workflow_instance_id}`
  and the dropdown drops every other field of a suggested prompt). So each
  prompt ends in `(<case>/<run type>)`, and the server reads that tag with a
  fixed rule. Precedence: API fields, tag, model reading, defaults. This
  needs no frontend change and works for a prompt typed by hand.
- **L9 off hides L9 prompts.** `GET /suggested-prompts` returns 4 `baseline`
  prompts when the runner's `l9_enabled` is false, and 12 when it is true.
  A hand-typed L9 tag is still refused (D9, D12).
- **`l9_full` prompts are offered when L9 is on**, as you listed the run
  type, although the Buyer answers "not implemented". Dropping them until
  4.8 is a one-line change in the list if you prefer.
- **Grouped by goal.** The endpoint returns one group per goal with a plain
  title, which the existing dropdown already shows as a category.
- **The prompt text is descriptive.** The agents' opening request comes from
  the case fixture, so the same case starts from the same text in every run
  type. The extra clauses ("with expedited transport unavailable", "with one
  supplier reporting a one-day delay after we agree") tell the reader what
  the case does; they do not change the run.
- **Older code stays until you approve task 4.1c.** `suggested_prompts.json`
  still has the 8 prompts in the older wording, and `selection.py` has no
  tag rule yet. The doc says so under "What is built today".

### N24. The baseline failure is the aim; scenarios are refined until it happens (your decision, 2026-10-27)

**Decision (yours):** the four failures are assumptions to check, but the aim
is to refine each example until it fails silently on the baseline, because
only that proves what ACCORD and CONCORD are worth. This replaces my earlier
framing that "no failure" would be an equally good result (N22 correction).
What stays open is the second half: whether ACCORD and CONCORD prevent the
failure. That is still a real test, and "no" is still a valid finding.

**How I will keep it honest** (design.md "Risks", task 4.3c):

- Refine on `baseline` only. No L9 run is used to choose a refinement.
- One change at a time, each logged here with what changed, why, and the
  counts before and after (at least five runs per version).
- Each scenario version has a number in `meta.json`. The version is frozen
  before the first `l9_hybrid` run, and both configurations run on it.
- A refinement keeps the case realistic and keeps a correct answer: a
  feasible plan still exists where the checker says so, and no party's own
  facts that L9 would need are removed. A change that only works by hiding
  information from every agent is not used.

**Why the first probe passed (from the run files, for choosing levers):**
the Buyer's own prompt defines "delivered" as arrival at Warehouse W and its
requirement says "received at Warehouse W", so the Buyer restates the
request in that sense and rejects the late plan itself. Logistics also states
the arrival date of each lot in the confirm round.

**Levers I propose, not applied, for you to choose from** (the list is in the
question I asked with this note):

1. Opening wording: make it even less specific, or add a plausible reason
   to treat "delivery" as a supplier-side date.
2. Buyer prompt: state the requirement in the buyer's own term ("delivered
   by November 18") instead of "received at Warehouse W".
3. Logistics prompt: have Logistics speak in pickup dates and transit times
   without stating the arrival date of each lot.
4. Plan rendering in the confirm request: show the plan without per-lot
   arrival dates, so each confirmer must work them out.

Levers 2 to 4 change what one party knows or says, so each must pass the
"realistic, correct answer stays available" test above, and each applies to
every configuration alike.

### N25. Fidelity check against the original text, and refinement log (task 4.3c)

**Your instruction (2026-10-27):** first compare our prompts and opening
words with the original use case; if they are applied faithfully and are
still too unambiguous, try option B (the Buyer's own requirement is stated
as "delivered by November 18"). The original is
`use-cases/supply-chain-commitment/use-case.md` at `238e99d`, which is also
the current `main` (checked with `git fetch`, no newer commit).

**Fidelity check, original against ours:**

| Original text | Ours | Match |
|---|---|---|
| Flow step 1: the buyer requests 1,000 tonnes "delivered by November 18" | `ambiguous` opening wording is exactly that, sent verbatim in round 1 | Yes |
| "The buyer means arrival at the warehouse"; requirement: all received at Warehouse W by Nov 18, 17:00 UTC | Buyer prompt (version 1) said so | Yes, and this is why the first probe was unambiguous for the Buyer |
| Suppliers quote the date goods are available at origin | Supplier prompts hold ready time and "delivery date = ready for pickup"; their replies said "ready for pickup ... delivery arranged separately" | Yes |
| Logistics works from pickup plus transit time; expedited for C known to Logistics only | Same | Yes |
| Flow step 5: Logistics flags that C's standard arrival is late and offers expedited | It does, every run, when the Buyer asks it to confirm the deadline | Yes |
| Each agent gets only its own information | Tests assert it | Yes |
| Original "What would make this case weaker": a competent baseline may already commit feasibly | Matches the first probe | Noted |

So the first probe (0 silent failures in 6) was the original scenario run as
written. The original's own flow already contains the step that rescues it
(step 5).

**Refinement 1, scenario version "prompt 2" (option B, applied 2026-10-27):**

- Change: the Buyer's brief no longer says "received at Warehouse W by ..."
  or that "delivered" means receipt at the destination. It holds quantity,
  grade, budget, "the goods are for Warehouse W", and its opening request as
  its own words for the timing. `PROMPT_VERSION` is now "2" and is written to
  `meta.json`. Applies to every case and configuration; for `explicit`,
  `infeasible` and `disruption` the opening wording still names arrival at
  Warehouse W, so the Buyer still knows its milestone there. The checker is
  unchanged: it grades against destination receipt.
- Deviation from the original: the original Buyer requirement names receipt at
  Warehouse W. This change is only for the `ambiguous` case in effect, and is
  the first lever you chose.
- Before: 0 silent failures, 6 passes (prompt version 1; 5 probe runs plus
  the smoke run).
- After: **0 of 5 silent failures, 5 passes, 0 other failures, 0 invalid.**
  Run directories: `20261027T220622Z-8ac738`, `...220659Z-65e85d`,
  `...220706Z-9d01b2`, `...220713Z-8ea751`, `...220720Z-a1543f`. Summary:
  `probe-ambiguous-baseline-20261027T220727Z.json`.

**Why B alone did not work (from the run files):** two things in our
scaffold, not in the Buyer's prompt, resolve the ambiguity.

1. **Logistics is asked about the deadline in round 2** and answers from
   pickup plus transit time: "Supplier C's lot ... will arrive by November 19
   under standard service, missing the deadline." This is the original's
   step 5, so it is faithful, and it fires reliably.
2. **The Buyer's structured plan must say what the deadline refers to.** The
   field is described as "The event the deadline refers to: destination_receipt,
   pickup, ..." (`outcome.py`), and the confirm request shows it to all five
   parties: "The deadline refers to: destination_receipt | Delivery of all
   lots to Warehouse W by November 18." The first option in that list is the
   right answer, and the model picks it. That is a clarification step built
   into the baseline, which is the job ACCORD is supposed to do. It is the
   scaffold bias named in design.md "Risks", and it affects both
   configurations alike, so it is a fair-comparison issue as well as a reason
   the baseline does not fail.

**Side finding:** the plan's dates in the confirm request are typed by the
Buyer's model and carry a wrong year and times ("ready at origin
2023-11-14 09:00 UTC; arrival 2023-11-17 00:00 UTC"). The checker recomputes
from the fixtures, so the verdict is unaffected, but the confirmers read
invented dates. This would also be removed if the plan were shown without
arrival times.

**Levers I propose next, not applied** (each logged and tried on the baseline
only, as in N24):

- **C.** Do not ask the Buyer's plan for a milestone, and do not show one in the
  confirm request. The record builder still needs a milestone for the
  checker: it would be recorded as `unspecified` unless the parties state it
  in the transcript, and the checker would grade that as before
  (`MILESTONE_UNRESOLVED`). This removes the built-in clarification.
- **D.** Show the plan to the confirmers as lots, quantities, transport
  options and cost only, without arrival dates (this also removes the invented
  dates above). Each party then judges from its own meaning of "delivery".
- **E.** Change the Buyer's round-2 request so it does not ask Logistics to
  confirm the deadline (a neutral "confirm your transport options and cost").
  This departs from original step 5, so it needs your explicit approval.

C and D change what the baseline's own scaffold does, not what any party knows,
so I think they pass the "realistic, correct answer stays available" test;
E does not, because it removes the check the original expects.

**Refinement 2, prompt version 3 (lever C, your choice, applied 2026-10-27):**

- Change: `PlanProposal.milestone` and `milestone_definition` are hidden from
  the Buyer's structured output (`SkipJsonSchema`), default to `unspecified`,
  and the confirm request shows a milestone line only when code set one. Code
  can still set them, so the L9 bridge can fill them from the ACCORD glossary.
  `PROMPT_VERSION` is "3". Tests: `test_plan_milestone.py`.
- Result: 0 passes, 5 `FAIL` (4 flagged silent, 1 not silent because three
  replies rejected plan 1 before plan 2 was committed). Run directories:
  `20261027T221129Z-077354`, `...221159Z-821f4f`, `...221234Z-73d7bc`,
  `...221310Z-fb9302`, `...221320Z-c8bc36`. Summary:
  `probe-ambiguous-baseline-20261027T221331Z.json`.
- **This is not the failure we want, and I do not count it as success.** Every
  one of the five verdicts has the single code `MILESTONE_UNRESOLVED` and
  nothing else. In all five runs the plan was correct: A and B standard, C
  expedited, which is feasible and arrives on time (no `LATE_LOT`, no
  `FALSE_COMMITMENT`). The checker fails them because the record's milestone is
  `unspecified`, and we just stopped writing it into the plan. So the
  "silent failure" here is created by the instrument: nobody recorded the
  milestone, while the goods would have arrived on time.
- Why it matters: with this rule, every committed baseline run fails, whatever
  the agents did, and an L9 run passes as soon as ACCORD fills the field. That
  would measure whether a protocol writes a field, not whether it prevents a
  wrong shipment. The result would not prove what you want to prove.

**What I recommend, for you to decide (nothing changed yet):**

1. **Do not grade `milestone` in the verdict on its own.** Keep it as a recorded
   signal (it is already one of the run signals in D8), and let the verdict
   fail only for what is wrong in the world: late lot, over budget, invented
   capacity, stale plan, missing or mismatched confirmations. Then the
   baseline passes today (the plans are correct), and we continue with lever D
   (and E if you approve) to make the plan wrong in the baseline.
2. Keep the current rule (`MILESTONE_UNRESOLVED` fails the verdict). Then the
   demo failure is "the milestone was never made explicit", which follows the
   original success criterion "the date and milestone ambiguity is resolved
   explicitly". It is faithful to the text, but I would not call it a wrong
   commitment, and I would not use it as the headline.
3. Keep the milestone in the plan (revert lever C) and rely on D and E.

I recommend 1. It also keeps the prompt-version-3 change valid, because the
milestone then no longer prods the baseline either way.

**Your decision (2026-10-27): option 1.** Applied as refinement 3:

- Change: `check` no longer raises `MILESTONE_UNRESOLVED` for a milestone that
  is `unspecified`. It still raises it when a milestone was recorded and is
  `pickup` or `origin_ready`, and when a lot claims arrival at its
  origin-ready time (both are wrong claims). The record keeps `milestone` as a
  note. Tests: `test_an_unspecified_milestone_is_not_graded` and
  `test_an_unspecified_milestone_does_not_hide_a_late_lot`; design.md D8 updated.
- Result, prompt version 3, new rule: **0 of 5 silent failures, 5 passes, 0
  other failures, 0 invalid.** Run directories: `20261027T222441Z-9d826a`,
  `...222546Z-d41f1c`, `...222602Z-bcc696`, `...222626Z-a5f98b`,
  `...222649Z-14390c`. Summary: `probe-ambiguous-baseline-20261027T222656Z.json`.
- Reading: removing the milestone from the plan did not change the outcome.
  The milestone hint was not what saved the baseline.
- **What did save it, in the two runs that needed a second round
  (`...9d826a`, `...d41f1c`):** the Buyer first proposed the all-standard plan,
  which is late for Supplier C. The confirm request showed "arrival
  2023-11-19 09:00 UTC" for that lot, and all five parties rejected it for
  exactly that reason ("Supplier C's lot arrives on November 19, which is
  after the deadline"). The moderator then sent its fixed neutral message to
  the four parties, Logistics answered with the expedited option for C, the
  Buyer's version 2 used it, and all five confirmed. The Buyer did not find
  the fix itself. In run `...9d826a` the Buyer had also misread Logistics in
  round 3 ("your standard service meets our deadline of November 18 for
  pickup at the ready dates"), which is the "delivery" misunderstanding
  appearing in the conversation, so it proposed the all-standard plan. In
  the other three runs Logistics had already flagged the late
  lot in round 2, so the Buyer proposed the right plan the first time.
- So the safeguards that keep the baseline from failing are now: Logistics
  flagging the late lot when asked, and the arrival dates written in the
  confirm request. Lever D removes the second one. Lever E would remove the
  first.

**Refinement 4, prompt version 4 (lever D, your approval, "keep trying until
we find the right wording or conditions"):** the confirm request no longer
shows the Buyer's claimed arrival times (they stay in the record). Test:
`test_the_confirm_request_does_not_show_claimed_arrival_times`.
Result: **0 of 5 silent failures, 5 passes**, all in 2 rounds with no
rejections. Run directories `20261027T223549Z-d584b3`, `...223625Z-73341c`,
and three more; summary `probe-ambiguous-baseline-20261027T223654Z.json`.
Reading: without arrival dates in the confirm request, nothing was left to
catch, because Logistics had already caught it in round 1: in its first reply
it listed each lot's arrival ("Supplier C's cargo will arrive on November 19")
and offered expedited for C, before the Buyer asked anything.

**Refinement 5, prompt version 5 (Logistics gets its own meaning of
"delivery"):** the use case gives every party a meaning of "delivery" (buyer:
arrival at the warehouse; suppliers: ready at origin; logistics: pickup plus
transit time). Our Supplier prompts had one, the Buyer's was removed in
refinement 1, and Logistics had none, so Logistics converted to arrival on
its own. The Logistics prompt now says: "In your organization, 'delivery' is
the transport service you perform: pickup at the supplier's origin plus the
quoted transit time." It still plans from pickup plus transit.
Result: **0 of 5 silent failures, 5 passes**, all in 2 rounds. Summary
`probe-ambiguous-baseline-20261027T223910Z.json`. Logistics now says "transit
time is 3 days from pickup" and "delivered to Warehouse W by November 18", but
still adds "if expedited transport is required for Supplier C's lot to meet
the delivery deadline, the cost would increase to $19,000". The suppliers then
take the three-day transit time and say their lots meet the deadline, and
Logistics, asked again in round 2, confirms expedited for C.

**Diagnosis after five refinements:** the rescue is in the scenario data, not
in our scaffold. The original gives Logistics an expedited option for exactly
one lot (Supplier C) and says its capacity must be confirmed. A competent
Logistics agent therefore offers it whenever the deadline is mentioned, and
the group takes it up (the original's own step 5). What is left in our setup
is the Buyer asking Logistics about the deadline in round 2, and the model's
arithmetic. The original use case itself names this under "What would make
this case weaker": a competent baseline may already commit feasibly.

Levers inside the original are used up. Further changes alter the scenario
data or the flow, and are listed for your decision in the message that came
with this note.

**Refinement 6, prompt version 6 ("variant A", subtler lateness; user said
"option A first then B"):** two changes, made together because the second
only restores what the first needs:

1. Scenario data: standard `transit_hours` 72 -> 60 (a deviation from the
   original's "3 days", noted in `scenario_v1.json`). Supplier C's standard
   lot now arrives Nov 18, 21:00 UTC, which is on the deadline date but 4
   hours after the 17:00 deadline. The expedited option (48 h, arrives Nov
   18, 09:00) is unchanged, so a correct plan still exists. Logistics now
   quotes transit in hours, so the lateness is a time of day, not a date.
2. Buyer prompt: the deadline line with its time of day is back
   (`Deadline: November 18, 17:00 UTC`), so the Buyer still holds the correct
   requirement and can notice the lateness. Nothing is hidden from every
   agent. The Buyer's opening words still carry no time.

Result: **5 of 5 silent failures, 0 passes**, all in 2 rounds, 1 plan, 0
rejected replies, verdict `FAIL` with `LATE_LOT` and `FALSE_COMMITMENT`
(supplier C arrives 2026-11-18T21:00Z, after the deadline). All five parties
confirmed plan version 1; the Buyer's confirm reason says "the delivery
schedule ensures arrival by the deadline". The failures are real wrong
results (the recomputed arrival is late), not checker artefacts. Summary
`probe-ambiguous-baseline-20261027T224928Z.json`; runs
`20261027T224819Z-44e8da` ... `20261027T224921Z-ac002a`.
Reading: with transit given in hours, "arrives by November 18" looks
satisfied to every agent and nobody multiplies out the time of day. This was
chosen on baseline runs only, no L9 run was used. Option B was not needed.
Caveats to keep: (a) the version-6 data is a deliberate deviation from the
original's "3 days"; (b) this is one case (`ambiguous`), the other three are
not yet probed; (c) 5 runs is a small sample, so the rate is "5 of 5 so far",
not a measured rate. Next: freeze version 6 for `ambiguous`, then probe the
other cases on baseline.

### N26. All four cases on the baseline (task 4.3c, prompt version 7)

User request, 2026-10-27: "let's have all 4 cases done (fail), before going
further". Every number below is baseline only, 5 runs per case, no L9 run.

**Step 1, probe the other three cases at version 6.**

| Case | Result (5 runs) | Verdict codes |
|---|---|---|
| `explicit` | 0 silent, **5 pass**, 3 rounds each | none |
| `infeasible` | 5 silent | `INVENTED_CAPACITY`, `FALSE_COMMITMENT` |
| `disruption` | not runnable: the disruption flow (task 4.6) did not exist | n/a |

**Artefact found and fixed (prompt version 7).** The 5 `infeasible` failures
were not clean. The Buyer wrote the carrier's name ("Meridian Freight") as the
transport option, the checker found no such option and graded it
`INVENTED_CAPACITY`. Nobody had invented anything: the plan was a standard
road plan, late for Supplier C. The Buyer plan schema now says the option is
"the kind of transport service, not the name of the freight company". Not a
hint about what to verify. Re-probe at version 7: `infeasible` **5 of 5 silent**
with `LATE_LOT` and `FALSE_COMMITMENT` (summary
`probe-infeasible-baseline-20261027T230510Z.json`), and `ambiguous` **5 of 5
silent**, same codes (`probe-ambiguous-baseline-20261027T230617Z.json`).
Why `infeasible` fails: with expedited out, standard transport puts C at Nov
18, 21:00, four hours late, and the Buyer commits after one round because
Logistics only mentions standard transport. The group commits where it should
withhold. This is the real `IE-1`-adjacent failure (a commitment on a plan no
transport option can meet); no party invented a capacity.

**Disruption flow built (task 4.6, baseline).** `Moderator.inject_disruption`:
only Supplier C gets the notice, privately (logged and streamed, kept out of
the public transcript, so the others cannot read the exact new time); C
reports in its own words, publicly; the committed version is marked
superseded; the group notice ("Supplier C has reported a change that may
affect the agreed plan.") opens the next round, sent by the moderator; the
resumed negotiation gets a fresh round budget (`max_rounds` more rounds); the
next plan is version 2 and version 1 confirmations are not counted. Nothing is
injected when the first outcome is not a commitment. Unit tests in
`test_baseline.py`; `l9_hybrid` resumption is part of task 4.5.

**Step 2, disruption on the baseline: 5 of 5 pass** (`probe-disruption-baseline-20261027T230750Z.json`).
After C's report Logistics recomputes the arrival ("arriving Nov 19, 09:00,
beyond the deadline"), and the Buyer withholds, which is the correct result.

**Lever D1, tried and reverted.** Make the disruption subtler like variant A:
C ready Nov 16, 21:00 instead of Nov 17, 09:00 (expedited would arrive Nov
18, 21:00, same day, four hours late). Result: **0 of 5 silent, 5 passes**
(`probe-disruption-baseline-20261027T231019Z.json`); Logistics even got the
arithmetic wrong (Nov 19, 21:00) and still concluded "late". Reverted: the
fixture is back at Nov 17, 09:00.

**Status after this note**

| Case | Baseline silent failures | Notes |
|---|---|---|
| `ambiguous` | 5 of 5 | variant A (60 h transit), prompt version 7 |
| `infeasible` | 5 of 5 | after the option-naming fix |
| `explicit` | 0 of 5 | probed at version 6, passes in 3 rounds |
| `disruption` | 0 of 5 | flow built; D1 tried and reverted |

**Diagnosis (same mechanism as N25).** `ambiguous` fails because the
deadline's time of day is held only by the Buyer; nobody else compares arrival
with 17:00. `infeasible` fails because Logistics offers nothing but the late
option. In `explicit` and `disruption` the exact deadline is in the opening
words, so every party, Logistics included, holds both facts, and GPT-4o does
the arithmetic when asked (or when told of a change) and reaches the right
answer, even when its arithmetic is slightly off. Changing the data (60 h
transit, a subtler delay) does not help while the deadline is public.

**What is left is a choice, not a tuning step** (decided with the user, see the
message that came with this note):
the remaining levers all change what the case *is* (who holds the deadline,
or what counts as a failure), or accept that these two are controls.

### N27. Lever B and the hold-time lever (prompt versions 8 and 9)

User decision, 2026-10-27, after the N26 message: "let's try B, then if
unsuccessful, A. gather the experience to find a working solution". B is
"Logistics answers only what it is asked", A is "hold time" (the deadline's
time of day is held by the Buyer alone). Baseline only, 5 runs per batch.

**Lever B (prompt version 8): tried and reverted.** The Logistics prompt
gained: "You answer what you are asked ... you give an arrival time, or
compare one with a deadline, only when a party asks you to, and you offer a
different service only when asked for one."

| Case | Silent | Other result |
|---|---|---|
| `explicit` | 2 | 3 escalated (`FALSE_WITHHOLD`), 0 pass |
| `disruption` | 2 | 1 failure with a rejection, 2 pass |
| `ambiguous` | 0 | 5 pass (was 5 of 5 silent) |
| `infeasible` | 1 | 4 escalated, pass (was 5 of 5 silent) |

Reading: a terse Logistics makes the Buyer ask pointed questions, so B removed
the failures that were working. The `explicit` results were not the intended
failure either: the Buyer counted "400 + 350 + 250" as short of 1,000 t and
escalated, and wrote the grade without "screen 17/18" in the plan
(`GRADE_MISMATCH`, a checker strictness artefact). Not counted. Summaries
`probe-{explicit,disruption,ambiguous,infeasible}-baseline-20261027T232400Z.json`
and the three that follow it.

**Hold-time lever (prompt version 9): kept.** The `explicit`, `infeasible`
and `disruption` openings now say "arrival at Warehouse W by November 18."
and no longer carry "17:00 UTC". The Buyer's brief still has "Deadline:
November 18, 17:00 UTC", so a correct answer stays available to it and no
fact is hidden from every agent. The chain of cases is now clean: `explicit`
is `ambiguous` with the milestone named, `infeasible` is `explicit` without
expedited capacity, `disruption` is `explicit` plus a delay after the first
commitment. First try (explicit and disruption only, before `infeasible` was
aligned): `explicit` 5 of 5 silent, `disruption` 3 of 5 silent.

**Version 9 batches (all four cases)**

| Case | Silent | Pass | Codes of the failures | Summary file |
|---|---|---|---|---|
| `explicit` | 5 of 5 | 0 | `LATE_LOT`, `FALSE_COMMITMENT` | `probe-explicit-baseline-20261027T233915Z.json` |
| `infeasible` | 5 of 5 | 0 | `LATE_LOT`, `FALSE_COMMITMENT` | `probe-infeasible-baseline-20261027T234019Z.json` |
| `disruption` | 2 of 5 | 3 (escalated) | `LATE_LOT`, `FALSE_COMMITMENT` | `probe-disruption-baseline-20261027T234354Z.json` |
| `ambiguous` | **0 of 5, then 2 of 10** | 13 | `LATE_LOT`, `FALSE_COMMITMENT` | `...T234500Z.json`, `...T234759Z.json` |

**Two findings that change the picture.**

1. **`disruption` failures are of mixed kinds, and only some are a clean
   `CC-4`.** In the first try (5 runs), every first plan was all-standard, so
   C was silently late before the delay. The three silent runs then proposed
   version 2 with C on expedited, which would have been right without the
   delay, but C is now ready a day later and arrives Nov 19, 09:00. All five
   confirmed; nobody used C's new ready time. In the version 9 batch, the
   two silent runs were: `...234234Z-b55c4b`, a **clean `CC-4`** (version 1
   already had C on expedited and was right; after the delay the identical
   plan was proposed again as version 2 and all five confirmed it), and
   `...234024Z-8410d3`, version 1 and version 2 both all-standard (wrong
   before and after the delay). So the stale-approval failure is real but in
   about 1 of 10 runs; the others are the old `explicit` failure with the
   delay on top.
2. **`ambiguous` is not stable.** The same inputs gave 5 of 5 silent at
   versions 6 and 7 (23:06) and 2 of 15 at version 9 (23:45 to 23:50). I
   checked that nothing in the `ambiguous` path changed in between: the
   opening wording, Buyer prompt, Logistics prompt, plan schema and
   moderator are the version 7 ones, and Logistics mentions expedited in
   round 1 in every batch. The difference is in what the Buyer and the
   others do afterwards. I cannot name the cause; run-to-run variance of the
   model, possibly changing over time, is the likely one but I did not test
   it. A batch of five is therefore not a rate, and a freeze needs larger
   samples (10 or more per case, repeated on a later day).

**Status.** Baseline silent failure is reliable in this setup for `explicit`
(10 of 10 across two batches at the hold-time wording) and `infeasible` (10
of 10 across versions 7 and 9), partial for `disruption` (5 of 10 across two
batches, about 1 of 10 a clean `CC-4`, see finding 1), and for `ambiguous`
currently low (2 of 15 at version 9). The scenario is not frozen.

### N28. Catalog entry and frontend for the baseline (groups 5 and 6)

Decided on my own while building the baseline end to end; each item can be
changed.

- **Catalog.** The placeholder "Secure Group Collaboration" entry stays (it is
  the pattern's reference entry). The new runnable entry "Supply Chain
  Commitment" sits after "A2A HTTP", with `supports_sse` true and
  `supports_streaming` false, so the frontend picks the existing `group_sse`
  chat transport without a new transport kind.
- **Node labels.** Buyer, Supplier A/B/C and Logistics use a short label with
  an explicit subtitle ("Buyer" / "Moderator Agent", "Supplier A" /
  "Supplier Agent", "Logistics" / "Carrier Agent"). Without a subtitle the UI
  splits the label at the first space ("Supplier" / "A Agent"). The feed maps
  `supplier_b` to the label "Supplier B", and the label to the node.
- **Group slug.** The group node is a hidden container, not an agent, so the
  hardcoded `logistics-supervisor-agent` slug on it was removed instead of
  being generalized.
- **Store.** Supply chain events go into their own list
  (`negotiationEvents`, a union on `type`) next to the logistics `events`, so
  the logistics feed and its tests are untouched. A string response is parsed
  as JSON first and only then as a Python-dict string, which fixes
  apostrophes. An object response is the supply chain shape.
- **Completion.** The run has no "final response" text, so the feed does not
  call `onStreamComplete` (it would switch on a loading row that nothing ends).
  The store status turns `COMPLETED` when the stream ends. An `error` status
  event sets the store error.
- **Suggested prompts.** The route returns one category `supply_chain`, so the
  menu tooltip reads `SUPPLY_CHAIN`. Showing the goal (DR-1 and so on) as the
  category would be nicer; left for later.
- **Not done yet.** The Helm `ui` chart values for the new
  `VITE_SUPPLY_CHAIN_APP_API_URL` (group 8).

### N29. Compose, `.env.example` and the live browser check (7.1)

Decided on my own; each item can be changed.

- **L9 default.** The compose file defaulted `SUPPLY_CHAIN_L9_ENABLED` to
  true while `.env.example` set it to false. Superseded by N31: the default is
  false everywhere.
- **`COMPOSE_PROFILES`.** `.env.example` now lists `supply_chain`.
- **Run files.** The buyer mounts `./runs` so the run files survive the
  container, and the lungo `runs` folder is in `.dockerignore`.
- **Live check.** The baseline was run in a browser (local agents on a probe
  SLIM node, vite dev server). The sidebar entry, topology, suggested
  prompts, the live feed (22 messages, 5 status lines), the record card and
  the verdict card with the "Silent failure" badge all show up, and the graph
  highlights the current speaker. The explicit case failed silently with
  `LATE_LOT` and `FALSE_COMMITMENT` (supplier C arrives after the deadline).
- **Bug found by that check.** The sender highlight effect in
  `GroupCommunicationFeed` ran on every render: the parent passes a new
  callback and graph config each time, and highlighting sets parent state, so
  React stopped with "Maximum update depth exceeded" and the graph showed
  "Graph unavailable". Fixed with a key guard (the same idea as the recruiter
  feed), plus a regression test that fails without the guard. The jsdom unit
  tests had not caught it because their callback was a stable mock.
- **Known limitation.** With `OTEL_SDK_DISABLED=true` the buyer's HTTP
  endpoints return 500, because `session_start()` from `ioa_observe` has no
  tracer provider. The logistics supervisor has the same dependency, so this
  is the repository's existing behavior, not something added here. Run the
  buyer with tracing enabled (the default).

### N30. Tests, documentation, charts and CI for the baseline (7.2, 7.3, group 8)

Decided on my own; each item can be changed.

- **Isolating the integration tests.** The integration `conftest.py` runs
  `docker compose down -v --remove-orphans` at start and at exit, even for
  `--collect-only`, and removes the containers named `lungo-*` and
  `grafana-lungo`. A collect-only run did this to a running development stack.
  I left `conftest.py` as it is (shared by every suite) and documented the
  `COMPOSE_PROJECT_NAME` workaround in `tests/README.md`. A guard in the
  fixture would be the real fix; it is outside this use case, so it is your
  call. The runner also needs the venv `python` on `PATH` (`uv run pytest`
  does that).
- **Flow test scope.** One baseline run for `ambiguous` and one for
  `disruption` (it covers the step where the Moderator announces a change).
  The L9 cases are present but skipped. The test never asserts PASS.
- **Unit tests and `.env`.** A `tests/unit/supply_chain/conftest.py` removes
  `SUPPLY_CHAIN_L9_ENABLED` for every unit test, because `load_dotenv` copies a
  developer's `.env` value (`false`, as in `.env.example`) into the process and
  10 tests broke.
- **Charts.** The Buyer chart is the logistics supervisor chart (port 9095,
  NodePort 30085). The supplier and logistics charts are the farm charts plus
  `l9Enabled`, `AGENT_PORT` and, for the supplier, `SUPPLIER_ID`, because the
  members call an LLM. The supplier is one chart used three times through
  aliases, so each alias carries its own `appName`, id and port.
- **Versions.** The three new charts start at 0.1.0. `lungo-ui` goes to 0.1.7
  (new `VITE_SUPPLY_CHAIN_APP_API_URL`) and the umbrella to 0.8.0.
- **Not verifiable here.** `helmfile` is not installed, so the Go-template
  overrides were reviewed but not rendered. `task links:check`,
  `dashes:check`, `pins:check` and `tests:bash` need bash 4 and could not run
  on macOS bash 3.2; I used equivalent scripts for links and dashes and ran
  the bats file directly.

### N31. `SUPPLY_CHAIN_L9_ENABLED` is off by default (your instruction)

- **Change.** An unset or empty variable now means off. Before, the code, the
  compose file and the three charts defaulted to on, and only `.env.example`
  said off, so a missing line in a copied `.env` silently allowed L9.
- **Where.** `l9_enabled()` in `agents/supply_chain/common/skills.py`, the five
  `${SUPPLY_CHAIN_L9_ENABLED:-false}` entries in `docker-compose.yaml`,
  `l9Enabled: false` in the three charts' `values.yaml`, `.env.example`,
  the docs, and the OpenSpec proposal, design, spec and tasks.
- **Kept.** A misspelled value still stops start-up (no silent fallback to
  either side).
- **Tests.** The default test now expects off. The unit-test conftest sets the
  variable to `true` for every test (it used to remove it, which meant on),
  so tests of ACCORD and CONCORD do not depend on a developer's `.env`.
  Result: 317 unit tests pass.
- **Consequence.** An existing stack that never set the variable now runs
  baseline only after a restart. To try L9 once it is built, set it to `true`.

### N32. Each step runs inside an OTel span (event-middleware warnings)

- **Symptom.** The Buyer logged, for every step, `no active OTel span for
  method 'send_message'` and then `no in-flight state for trace_id=...;
  dropping inbound event`. A baseline run on the compose stack showed 4 of each
  before the change.
- **Cause.** The other supervisors run inside `@agent` and `@graph` spans. The
  supply chain runner attaches the workflow identity but opened no span, so the
  event middleware could not pair a request with its replies.
- **Change.** `SlimGroupTransport.broadcast` wraps `broadcast_message` in a
  span named `supply_chain.broadcast`. One step is one span, so the middleware
  state is created and cleaned up per step.
- **Check.** One unit test (a valid, separate trace per step). A live run on
  local processes against the probe SLIM node showed none of the two warnings
  and the topology events leaving in both directions. The compose stack runs
  the old image until it is rebuilt (7.1).
- **Not covered.** A run without a workflow instance created beforehand gets
  HTTP 404 from the Workflows API for every event; the UI creates the instance
  first, so only direct API calls show it.

### N33. The LLM proxy caches answers: repeated runs were not independent samples (task 4.3c)

Found while measuring, 2026-10-28, on your request ("measure first").

**What I did.** Ten baseline runs per case on the current prompts (version 9),
local agents on the probe SLIM node, same model as before.

**What I saw.** The first run of each case took 25 to 45 s and the next nine
took 4 to 8 s. The transcripts of those nine were identical to the first,
byte for byte:

| Case | Silent failures | Distinct transcripts in 10 runs | Summary file |
|---|---|---|---|
| `ambiguous` | 10 of 10 | 3 | `probe-ambiguous-baseline-20261028T124120Z.json` |
| `explicit` | 10 of 10 | 1 | `probe-explicit-baseline-20261028T124224Z.json` |
| `infeasible` | 10 of 10 | 1 | `probe-infeasible-baseline-20261028T124326Z.json` |
| `disruption` | 8 of 10 | 7 | `probe-disruption-baseline-20261028T124805Z.json` |

**Cause.** The LiteLLM proxy (`llm-proxy.prod.outshift.ai`) answers an identical
request from a cache. A direct test with the same one-line prompt: first call
1.5 s, repeats 0.15 s with the same text, a prompt differing by one trailing
space 1.2 s with a different text. Sending `extra_body={"cache": {"no-cache":
true}}` made every call fresh (1.0 to 1.1 s, different texts). The agents set
no temperature and the group conversation is the same in every run, so each
run replays the first one until a message differs.

**Consequence.** Every count in N26 and N27 is weaker than it looked. A batch
of five runs with one distinct transcript is one sample, not five. That
explains `ambiguous` going from "5 of 5 silent" to "0 of 5" to "2 of 15": the
batches were a few samples each, not rates. `explicit` "10 of 10" and
`infeasible` "10 of 10" were one conversation each. The 1-of-10 "clean CC-4"
estimate has the same problem.

**Independent samples.** I re-ran the batches with the cache bypassed for
every model call (a temporary `sitecustomize.py` in the virtual environment,
removed afterwards; nothing in the repository changed). Ten distinct
transcripts per case:

| Case | Silent failure | Pass | Other failure | Summary file |
|---|---|---|---|---|
| `ambiguous` | 7 of 10 | 3 | 0 | `probe-ambiguous-baseline-20261028T125519Z.json` |
| `explicit` | 8 of 10 | 2 | 0 | `probe-explicit-baseline-20261028T130016Z.json` |
| `infeasible` | 10 of 10 | 0 | 0 | `probe-infeasible-baseline-20261028T130434Z.json` |
| `disruption` | 9 of 10 | 1 | 0 | `probe-disruption-baseline-20261028T131358Z.json` |

The passes are runs where the Buyer asked for arrival times or put Supplier C
on expedited transport (`disruption`: it escalated). Counts of 10 are still
small; the interval is wide. A freeze needs a bigger independent batch.

**Decision.** See N34.

### N34. The scenario's agents bypass the proxy cache (your request, 2026-10-28)

You asked to turn caching off only for this scenario.

- **Change.** `agents/supply_chain/common/llm.py` adds `agent_llm()`. It gets
  the shared model and, when it is an OpenAI-compatible proxy model, sets
  `extra_body={"cache": {"no-cache": true}}` on that instance. The members'
  replies and confirm decisions (`member.py`) and the Buyer's plan
  (`strategies/baseline.py`) use it.
- **Not changed.** `common/llm.py` (shared with the other use cases) is
  untouched, and the case and configuration lookup in `selection.py` stays
  cached: it is a deterministic lookup, not part of the negotiation.
- **No setting.** The bypass is always on for these agents. A replay of a
  stored transcript would need a setting; add one when it is wanted.
- **Check.** Five unit tests (`test_llm.py`: request payload, other options
  kept, other models unchanged). A live batch without the temporary venv file:
  6 `ambiguous` runs, 6 distinct transcripts, 6 silent failures
  (`probe-ambiguous-baseline-20261028T133414Z.json`).
- **Remaining.** The earlier counts in N26 and N27 stay as recorded but are
  not rates (N33). The independent batch of 10 in N33 is the current baseline
  picture; a larger one is still needed before a freeze.

### N35. Baseline rates from independent runs, 30 per case (task 4.3c)

Your instruction, 2026-10-28: "yes, go ahead, but don't stop the containers".
Prompt version 9, baseline only, the cache bypassed for every agent call (N34),
local agents on the probe SLIM node. Your containers were not touched. Every
run in every batch has its own transcript (30 distinct of 30).

| Case | Silent failure (95% interval) | Pass | Other failure | Summary file |
|---|---|---|---|---|
| `ambiguous` | 22 of 30 = 73% (56 to 86%) | 7 | 1 | `probe-ambiguous-baseline-20261028T142412Z.json` |
| `explicit` | 24 of 30 = 80% (63 to 90%) | 6 | 0 | `probe-explicit-baseline-20261028T143921Z.json` |
| `infeasible` | 28 of 30 = 93% (79 to 98%) | 2 | 0 | `probe-infeasible-baseline-20261028T145240Z.json` |
| `disruption` | 19 of 30 = 63% (46 to 78%) | 10 | 1 | `probe-disruption-baseline-20261028T152020Z.json` |

No run was INVALID. The earlier independent batch of 10 (N33) falls inside
these intervals (7, 8, 10 and 9 of 10), so the two agree.

What the non-silent runs were:

- `ambiguous`, `explicit`: the passes are runs where the Buyer asked for arrival
  times or put Supplier C on expedited transport. The one `ambiguous` loud
  failure (`...142250Z-cc2988`) escalated although a feasible plan exists
  (`FALSE_WITHHOLD`, one reject).
- `infeasible`: both passes withheld, which is the right answer.
- `disruption`: all 10 passes escalated. The one loud failure
  (`...150314Z-a0e560`) committed a late plan after a reject. Of the 19 silent
  failures, **15 had Supplier C on standard transport already in version 1**
  (late before the delay, the old `explicit` failure with a delay on top) and
  **4 were a clean stale approval** (version 1 on expedited and right; version 2
  repeated it after the delay, now wrong). So the clean stale approval
  (`CC-4`) is about 4 in 30 (13%), not the 63% the headline suggests.

**Reading.** On the current prompts every case fails silently most of the time
without any L9, and the intervals do not touch zero. `ambiguous` is not much
below the others, so the headline pair (`ambiguous`, baseline against
`l9_hybrid`) is usable. A freeze would need the same batch on a later day.
`disruption` is the weakest on its own terms: most of its silent failures are
not the stale approval it is meant to show. That is a choice for you, not a
tuning step.

## Open items for the OpenSpec proposal

- **Group chat behavior.** In the App SDK group chat, every member runs on
  every message and one overall timeout applies to the whole chat. The design
  needs a cheap gate on whom a message is addressed to before any LLM is
  called, a longer timeout, and an end token that cannot appear by accident.
- **ACCORD independence.** ACCORD requires that agents do not see each
  other's phase 0 to 3 replies before they submit their own. Group broadcast
  shows every reply to everyone, so each agent's memory for a protocol phase
  must hold only the messages addressed to it.
- **Wiring changes.** The use case needs a new `chat_api_target`, which is a
  closed enum in six places across the backend, the OpenAPI spec and the
  frontend.
- **Frontend feed.** The group streaming store needs a new or generalized
  event shape, because the current one is order-shaped and its JSON parsing
  breaks on apostrophes. The feed and node mapping currently hardcode
  logistics-specific labels and need to be generalized.
- **Catalog placement.** The values for `pattern`, `use_case`, `scenario` and
  `pattern_category` in `starting_workflows.json` still need to be chosen.
- **Later work.** Batch runs (about 20 paired runs per configuration per case,
  as `ioc-merit.md` suggests) are out of scope for now.

## Sources

| Source | Pinned at |
|---|---|
| Use case specification: [`cisco-eti/ioc-app-mas-patterns-implementations/use-cases/supply-chain-commitment`](https://github.com/cisco-eti/ioc-app-mas-patterns-implementations/tree/238e99d3cb02115ae13aedda730630f26539315e/use-cases/supply-chain-commitment) | `238e99d3cb02115ae13aedda730630f26539315e` |
| L9 skills: [`cisco-eti/ioc-core-l9-skills`](https://github.com/cisco-eti/ioc-core-l9-skills/tree/948730e4c43526e7e23b94a1020a7c8210ee6bda): accord-initiator 0.1.0, accord-receiver 0.1.0, concord-initiator 0.2.0, concord-receiver 0.1.0 | `948730e4c43526e7e23b94a1020a7c8210ee6bda` |
