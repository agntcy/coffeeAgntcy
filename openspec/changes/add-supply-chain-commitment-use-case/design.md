# Design

## Context

See proposal.md for the reasons behind this change. The requirements are in
`specs/supply-chain-commitment/spec.md`.

Current state that shapes the approach. All paths are under
`coffeeAGNTCY/coffee_agents/lungo/`:

- **The Group Messaging (logistics) workflow is the template.** The
  supervisor (`agents/supervisors/logistics/`) uses the App SDK to open a
  SLIM group (`start_streaming_groupchat`) and streams NDJSON to the UI. The
  group members (`agents/logistics/*`) are keyword state machines with no
  LLM.
- **App SDK group semantics, confirmed in the installed 0.6.0 (task 1.1):**
  - in `start_streaming_groupchat`, the initiator publishes only the first
    message and then only listens;
  - every message goes to every member, and each member runs its executor on
    every message, one at a time;
  - the A2A server's `handle_message` always returns a reply (an error
    payload at worst), and the reply is broadcast to the group, so members
    also answer each other's replies;
  - a single overall timeout covers the whole chat;
  - the chat ends when any message contains the `end_message` substring.
- **`broadcast_message(..., recipients=[...])` over SLIM** opens an MLS group
  session with the recipients, sets `x-respond-to-source`, and collects one
  reply per recipient. Recipients answer only the sender.
- **`chat_api_target` is a closed enum** in six places across the backend,
  the OpenAPI spec and the frontend.
- **The frontend group store is order-shaped.** It requires `order_id`,
  `state` and `"DELIVERED"`. It parses Python-repr dicts by replacing every
  `'` with `"`, so text containing an apostrophe breaks.
- **The topology identity map hardcodes the group node's directory slug** to
  `logistics-supervisor-agent`.
- **The L9 skills are stdlib-only Python scripts plus `SKILL.md` texts.**
  Initiators keep state in files. `concord_initiator.py init` creates its
  own state path. Receivers reply with output from `concord_receiver.py
  forge`.
- **The repo dash check scans everything.** The upstream `SKILL.md` files
  contain em dashes.

## Goals / Non-Goals

**Goals:**
- Show a silent cognitive failure on purpose: in the `ambiguous` case
  without ACCORD and CONCORD, a run in which the process is clean, all five
  parties confirm, nobody objects, and the checker still says `FAIL`. Then
  run the same case with L9 to see whether it prevents the failure (D12).
  The result is reported as observed, with counts, never selected.
- A run whose outcome can be traced back to agent cognition, not to
  scaffolding. The same prompts, fixtures and model are used across
  configurations, and the same deterministic checker grades every run.
- An L9 hybrid that follows the protocol exactly as the scripts define it,
  so that a failure we observe is not caused by protocol drift.
- An architecture where `l9_full` can be added later by adding one strategy
  and some agent tools, without changing the transport, the record, the
  checker or the UI.

**Non-Goals:**
- Implementing `l9_full`. It is declared and rejected for now.
- Batch experiments or statistics (for example, 20 paired runs per cell),
  and the structured-schema configuration from `ioc-merit.md`.
- Real carrier, ERP or purchasing integration. Everything is simulated.
- Changing the logistics workflow's behavior. Only the shared frontend code
  is generalized, and logistics must keep working unchanged.

## Decisions

### D1. Layout and naming

| Piece | Location / name |
|---|---|
| Buyer (supervisor + chat API, port 9095) | `agents/supervisors/supply_chain/` |
| Supplier agent, one codebase, three instances (`SUPPLIER_ID=a,b,c`, ports 9096-9098) | `agents/supply_chain/supplier/` |
| Logistics agent (port 9099) | `agents/supply_chain/logistics/` |
| Shared code: envelope, fixtures, record model, checker, L9 bridge, role prompts | `agents/supply_chain/common/` |
| Fixtures | `agents/supply_chain/fixtures/scenario_v1.json` |
| Vendored skills | `third_party/l9_skills/<skill>/` + `third_party/l9_skills/PROVENANCE.md` |
| Run artifacts | `runs/supply_chain/<run_id>/` (gitignored; overridable by `SUPPLY_CHAIN_RUN_DIR`) |
| `chat_api_target` | `supply_chain` |
| UI base URL env | `VITE_SUPPLY_CHAIN_APP_API_URL` (default `http://127.0.0.1:9095`, kind NodePort 30085) |
| Compose profile / Helm charts | `supply_chain`; `supply-chain-buyer`, `supply-chain-supplier` (aliased three times in `local-cluster`), `supply-chain-logistics` |

Running one supplier codebase three times means the suppliers cannot differ
by implementation, only by fixture slice. This keeps the comparison fair.

### D2. Information boundary is enforced by data loading

Each agent process loads only its own slice of the fixture: the Buyer gets
`buyer` plus `case.buyer_wording`, a supplier gets `suppliers[<id>]`, and
Logistics gets `logistics` plus `case.logistics_overrides`. The run sends
only the case id to each agent, and each agent resolves its slice locally.
This is the cross-organization boundary. A unit test checks that no other
party's values appear in a role's rendered prompt.

### D3. Buyer-moderated group sessions and the message envelope

**Transport (decided after the task 1.1 spike, user decision of
2026-10-27):** the moderator delivers each step with the A2A client's
`broadcast_message(request, recipients=[...])` over SLIM. The SDK opens an
MLS group session with the addressed agents, and each addressee replies to
the moderator only. A step addressed to one agent is a one-member broadcast,
so all steps use the same path. Each step uses a SLIM channel name of its
own (`lungo/agents/scc-<run_id>-<seq>`): the live check of task 4.2b showed
that reusing one name across steps with different invitees can lose a later
step. The Buyer's own persona is not a SLIM recipient; the moderator calls
it in process. A request addressed to it is sent with sender `moderator`,
because a member ignores requests whose sender is itself. Every request carries the public transcript
the agent is allowed to see (D5 restricts this for ACCORD), which makes the
logical group shared even though replies are not fanned out by the SDK.

`start_streaming_groupchat` was rejected for this workflow, because the
initiator cannot publish after the first message and every member answers
every message, including other members' answers. With LLM members, that
traffic grows geometrically until the timeout. Suppressing it would need a
patch to the SDK's private A2A server callback.

Every message is a JSON text part:

```json
{"scc": 1, "run_id": "...", "seq": 12, "from": "supplier_b",
 "to": ["buyer"], "kind": "negotiation", "phase": "round_2",
 "plan_version": 1, "reply_to": 11, "case": "explicit",
 "configuration": "baseline", "body": "...", "transcript": [...]}
```

`case` and `configuration` tell a member which fixture slice to load (D2).
`transcript` holds the public messages that member may see for this step,
since replies are not fanned out by the SDK.

The `kind` field takes one of these values:

| `kind` | Purpose |
|---|---|
| `negotiation` | A free-text negotiation turn |
| `accord_request` / `accord_reply` | An ACCORD phase message and its answer |
| `concord_request` / `concord_reply` | A CONCORD protocol message and its answer |
| `confirm_request` / `confirm_reply` | Asking a party to confirm a plan version, and its answer |
| `event` | An injected event such as the disruption, sent by the moderator |
| `control` | `RUN_END` |

A member that receives an envelope whose `to` does not contain its id
replies with a fixed `{"kind": "noop"}` without calling its LLM. With
broadcast delivery this should not happen. The gate is a guard, and the
moderator drops noops from the stream and the transcript.

`seq` is assigned by the Buyer, which acts as moderator. A member's reply
echoes the `seq` of the request it answers, and the moderator gives the
reply its own `seq`. The end token is `"control": "RUN_END"` inside a JSON
string the moderator emits. LLM output is always JSON-encoded inside
`body`, so an agent cannot end the chat by accident.

**Alternatives considered:**
- A self-running group chat, with a wrapper around the SDK's private
  callback so unaddressed members stay silent. Rejected, because it depends
  on SDK internals.
- Plain unicast `send_message` per agent. Not needed, because broadcast
  with one recipient covers it and keeps every step in a SLIM group
  session.

### D4. Turn structure is set by the moderator, the content by the LLMs

The Buyer process holds a run loop (the moderator). The loop decides who is
addressed next. The agents decide what to say.

- **`baseline`:**
  1. The Buyer's LLM opens with the fixture wording.
  2. Each round addresses Supplier A, B, C, then Logistics, then the Buyer.
     Each agent sees the public transcript so far.
  3. After each round the Buyer's LLM returns one of `continue` (with a
     message), `propose_plan` (a structured plan), `withhold` or
     `escalate`.
  4. A proposed plan goes to a confirm round (D6).
  5. The run stops at the round limit (`SUPPLY_CHAIN_MAX_ROUNDS`, default 6).

  Role prompts are plain role prompts: each agent is told to represent its
  organization, with its own facts and its own meaning of "delivery". They
  carry no guardrail lines (no "only agree to what you can honor", no "say
  so instead of guessing"; user decision of 2026-10-27). No protocol
  vocabulary is used.
- **`l9_hybrid`:** see D5.

In both configurations the role prompts share one base text per role. L9
adds the receiver `SKILL.md` text and the forge tool on top of it. The role
prompts carry a `PROMPT_VERSION`, written to every run's `meta.json`, so a
scenario refinement (task 4.3c) is traceable. Version 2: the Buyer states its
timing requirement only in its own opening words.

### D5. L9 hybrid bridge

`agents/supply_chain/common/l9_bridge.py` wraps the vendored scripts. It
calls them as `subprocess.run([sys.executable, <script>, ...args],
input=..., capture_output=True, timeout=...)`. There is no shell, and the
state files live under the run directory.

**ACCORD:**
- The specialists are all five agents. The Buyer takes part as a specialist
  through its own LLM persona, separate from the moderator.
- The initiator choices are made by the Buyer's LLM, using a prompt built
  from `l9-accord-initiator/SKILL.md`, through structured output:
  - `init`: the incident text, `key_terms` and `action_tool`
    (`commit_plan`);
  - VERIFY: `REQUIRED_KNOWLEDGE` and `OBJECTIVE_CLAUSES`;
  - EXECUTION: one assignment per specialist.
- The code fills the phase request templates from the SKILL.md word for
  word and follows `next_command`.
- `FLAGGED` contracts continue, as the skill specifies, and are recorded.
- The CLARIFY round runs only if the script returns a non-empty `ambiguous`
  list. Upstream currently always returns an empty list, so a flagged
  "delivery" term stays flagged. This is a property of the protocol that we
  observe, not one we fix.

**CONCORD:**
- `init` is run with `--agents buyer,supplier_a,supplier_b,supplier_c,logistics`.
- The schema, context, `--x-reject` and `--x-ideal` come from the Buyer's
  LLM (initiator SKILL.md rules), and the context includes the locked
  contract and the execution replies.
- `--satisfaction-threshold` defaults to `SUPPLY_CHAIN_CONCORD_THRESHOLD`
  (0.7) and `-B` to `SUPPLY_CHAIN_CONCORD_BUDGET` (6).
- The code sends each printed message block unchanged to the named agents,
  calls `record-reply` with each raw reply, and follows `REJECTED` blocks
  using the skill's one-retry rule (`mark-missing` in the score phase).
- After `Phase: Complete`, the commit message is broadcast to everyone.
  The Buyer's LLM then turns the outcome into `propose_plan`, `withhold` or
  `escalate`.

**Receivers:**
- Each agent runs a small LangGraph graph: a model node bound to the
  tool, a `ToolNode` (the pattern from the auction supervisor), and a loop
  between them, limited to 6 tool rounds. `ToolNode` returns tool errors to
  the model, so a malformed tool call does not end the reply.
- The prompt holds the role text plus the matching receiver SKILL.md: the
  ACCORD receiver for `accord_request`, the CONCORD receiver for
  `concord_request`.
- One tool is exposed: `concord_forge(subcommand, arguments)`. It runs
  `concord_receiver.py forge` without a shell, refuses `@file` arguments
  (the script would read the file into the reply), and returns its stdout. The reply body for a
  CONCORD message is the forge stdout. If the LLM's final text is not forge
  output, the reply is still sent as the agent produced it, so that
  `record-reply` rejects it as the protocol intends.

**Memory independence:**
- An agent's prompt for an ACCORD phase message contains only the messages
  addressed to that agent in the current protocol (not peers' replies),
  together with its own earlier replies.
- For CONCORD, the prompt keeps the agent's own anchor exchange and all
  messages addressed to it (repair messages carry the scores, by design).

**Alternatives considered:**
- Hardcoding the key terms or anchors in code was rejected, because it
  would give the agents the answer.
- Running the scripts in-process through imports was rejected, because the
  CLI is the skill's contract and importing would couple us to internals.

### D6. Confirmation, plan versions and the record

A plan proposed by either configuration gets a new `plan_version` and a
`confirm_request` to all five parties. Each party's LLM replies `confirm` or
`reject` with a reason, using its own data. The record builder takes the plan
from the Buyer's structured output, the confirmations from the replies whose
`plan_version` matches, and the evidence references from `seq` numbers.

The status is set as follows:
- `committed` only if the Buyer commits and all five confirm the same
  version;
- `withheld` if the Buyer withholds or a party rejects and the round limit
  is hit;
- `escalated` if the Buyer escalates.

The record is a Pydantic model in `common/record.py` and is also exported as
JSON Schema next to the fixtures.

### D7. Disruption

When the first outcome is `committed` in case `disruption`:
1. The moderator sends an `event` to Supplier C (its slice now says ready
   Nov 17, 09:00 UTC). The event is private: it is logged and streamed but
   kept out of the public transcript, so the other parties learn the change
   only from Supplier C's own report. The committed version is marked
   superseded.
2. Supplier C's LLM reports the change in its own words (public).
3. The moderator opens the next round with the group notice ("Supplier C has
   reported a change that may affect the agreed plan."). Negotiation resumes
   with `plan_version + 1`, a fresh round budget of `max_rounds`, and no
   confirmations carried over:
   - in `baseline`, with more rounds;
   - in `l9_hybrid`, with a new CONCORD run under the existing locked
     contract. Per ACCORD rule 4, the contract is not reopened, and
     conflicts are noted as `FRAME_CONFLICT`.

The final record is the latest version. Earlier versions are kept in the run
files.

### D8. Checker

`common/checker.py` is a pure function: `check(record, fixtures, case) ->
Verdict`. It recomputes each lot's arrival time (ready time plus the transit
of the chosen option, where the option must exist and be available in the
case) and the total cost from the fixtures. It compares these to the
deadline and budget. The expected outcome is not a hardcoded table: the
checker enumerates every usable option per lot in the effective case (after
the disruption when one was injected) to decide whether a feasible plan
exists.

- `FALSE_COMMITMENT` is added to a committed record when no feasible plan
  exists, or when a plan-content code is present (`LATE_LOT`,
  `OVER_BUDGET`, `QUANTITY_MISMATCH`, `GRADE_MISMATCH`,
  `INVENTED_CAPACITY`, `STALE_PLAN`). Confirmation gaps
  (`MISSING_CONFIRMATION`, `VERSION_MISMATCH`) and `MILESTONE_UNRESOLVED`
  fail the verdict on their own.
- `STALE_PLAN` is raised when a disruption was injected and the committed
  plan was never superseded.
- The per-lot split of the $15,000 standard total ($5,000 each) is a
  fixture assumption that reproduces both upstream totals.

- `MILESTONE_UNRESOLVED` is raised when the record's milestone was
  recorded and is not destination receipt (`pickup` or `origin_ready`), or
  when a claimed arrival time equals the origin-ready time. A milestone
  that is `unspecified`, because nobody wrote it down, is not graded and is
  kept in the record as a note (user decision of 2026-10-27, decisions N25).
  Otherwise a correct plan would fail only for a missing field, and an L9
  run would pass only by filling that field in. The baseline plan no longer
  asks for the milestone, so baseline records carry `unspecified`.
- The run also records signals that are not part of the verdict: whether
  "delivery" was among the ACCORD key terms, the glossary status of
  "delivery", the contract status, the CONCORD outcome, the number of
  rejected replies, token usage and latency.

The checker runs in the Buyer process after `RUN_END`, and its result goes
only to the stream and the run files. It is not a graph node.

**Process health and outcome correctness are separate axes.** The verdict
grades the outcome against the fixtures, never the communication process. A
run in which every step got its replies and everyone confirmed, but the
plan arrives late, is `FAIL`, not `PASS`.

- `INVALID` is a third verdict. `check` returns it when the record's reason
  is `timeout` or `protocol_error`, before any other grading, so an outage
  or a script error is not counted as `FALSE_WITHHOLD` or any other
  cognitive failure. A cancelled run has no record and no verdict. In run
  summaries, invalid and cancelled runs are counted separately and never as
  `PASS` or `FAIL`. A `round_limit` stays graded, because agents failing to
  converge is behavior we want to observe.
- `silent` is a flag on the run result, not an input of `check`, so `check`
  stays a pure function of the record and the case. The run computes it from
  the verdict, the record and the run signals: status `committed`, one
  `confirm` from each of the five parties for the recorded version, no
  rejected reply anywhere in the run, no escalation, and verdict `FAIL`.
  The streamed verdict event and the run files carry it.

### D9. API and prompt selection

The new routes are:
- `POST /agent/prompt` and `POST /agent/prompt/stream` accept optional
  `case` and `configuration` fields, which take precedence;
- `GET /suggested-prompts` returns the prompts grouped by goal (one group
  for each of `DR-1`, `CE-1`, `IE-1` and `CC-4`, with a plain-language
  title). Each prompt is an order written for a person, ending in a tag
  `(<case>/<run type>)`. With `SUPPLY_CHAIN_L9_ENABLED` on the response has
  12 prompts (four cases times `baseline`, `L9 hybrid`, `L9 full`); with it
  off, 4, all `baseline`, so the chat never offers an L9 option (D12). The
  list is filtered by the runner's `l9_enabled`, which is read once at
  start-up. The mapping and the wording are in
  `docs/supply_chain_suggested_prompts.md`;
- `/agents/{slug}/oasf`, `/health` and `/v1/health`, as in logistics.

A request that names `l9_hybrid` or `l9_full` in the `configuration` field
while `SUPPLY_CHAIN_L9_ENABLED` is off is rejected with HTTP 400 and a
message that says L9 is disabled in this deployment (D12). When the prompt
asks for L9 instead, the stream's first event states the selection and the
second is a `status` event with state `l9_disabled`, and the run ends. Either
way no agent is contacted and no run directory is created.

Selection precedence, highest first:
1. the `case` and `configuration` fields of the request;
2. the closing tag of the prompt, `(<case>/<run type>)`, read by a fixed
   rule (a regular expression on the last parenthesised group, case
   insensitive). Run types are written `baseline`, `L9 hybrid` and `L9 full`;
   the identifiers `l9_hybrid` and `l9_full` are accepted too. A tag with an
   unknown case or run type is ignored and the next level applies. The
   suggested prompts carry this tag, so choosing one sets the case and the
   configuration without a model and without any frontend change (the chat
   sends only the prompt text);
3. an LLM with `with_structured_output` (using enums), for a prompt typed
   without a tag, the same way logistics extracts order parameters. It
   fills only the field the tag did not give;
4. the defaults, `ambiguous` and `baseline`, with a note in the first event.

The prompt text is for the reader. The Buyer's opening request always comes
from the case fixture (D4), so a prompt's listed conditions do not change
what the agents are asked. A unit test checks that every suggested prompt's
tag equals its `case` and `configuration` fields.

The stream emits `json.dumps` lines in this shape:

```json
{"response": {"type": "message|record|verdict|status", ...}, "session_id": "..."}
```

### D10. Frontend

- Add `supply_chain` everywhere `chat_api_target` is enumerated, and
  regenerate the OpenAPI TypeScript.
- Generalize the group streaming store with a discriminated union. The
  existing `LogisticsStreamStep` stays as it is. A new
  `SupplyChainStreamEvent` is selected when the response has a `type`
  field. Parsing tries `JSON.parse` first and keeps the quote-replace
  fallback only for the logistics Python-repr payloads.
- `GroupCommunicationFeed` renders the negotiation messages (sender to
  addressees, phase badge), a record card and a verdict card (`PASS`/`FAIL`
  with failure codes). The node highlight maps senders by node label.
- The group node slug comes from the workflow's `chat_api_target`, or from
  the group node's `agent_record_uri` when present, instead of the
  hardcoded logistics slug.

### D11. Vendoring and the dash check

The four skill folders are copied byte for byte. `PROVENANCE.md` records the
upstream URL, the commit `948730e`, the skill versions, the copy date, the
"no upstream licence; do not push" note, and a `sha256sum` manifest that a
unit test verifies. `check_dashes.bash` and `fix_dashes.bash` pass
`--exclude-dir third_party` (D1 path), and their bats tests cover the
exclusion. `find_strings.bash` previously applied `--exclude-dir` and
`--exclude-glob` only outside git, so it now turns them into git exclude
pathspecs for both tracked and untracked files. No caller used those flags
in git mode before. The root `.gitignore` gains
`/coffeeAGNTCY/coffee_agents/lungo/runs/`.

### D12. Keeping ACCORD and CONCORD out of the failing run

Two levels, which combine as follows:

| Level | Set where | Controls |
|---|---|---|
| Capability | `SUPPLY_CHAIN_L9_ENABLED` (default `false`), one variable in the Compose `.env` passed to all five services, and one chart value for each of the three Helm charts | Whether the deployed agents can do ACCORD and CONCORD at all |
| Run | The `configuration` field in the API, or the prompt | Which negotiation one run uses |

- **Switch on:** each run names its configuration. A `baseline` run and an
  `l9_hybrid` run follow each other with no restart, on the same model,
  prompts and agents. This is how the paired demo runs.
- **Switch off:** every run is forced to `baseline`. `l9_hybrid` is rejected
  by the Buyer (D9). The suggested prompts offer only the four `baseline`
  prompts, so a person using them cannot reach an L9 run. A member that still receives an `accord_request` or
  `concord_request` raises an error, so the sender sees a failed step (a
  `protocol_error` run, graded `INVALID`) and a deployment where only some
  agents have L9 on cannot pass for a working run. The member does not read
  the skills directory or call its model. The forge tool is not created, and the skill text is not
  put into any prompt. This is the mode for showing that L9 is absent.
- The switch alone does not select a configuration. It only locks the
  choice. A single environment variable that fixed the configuration would
  need a restart between the two demo runs and would prevent a paired run in
  one UI session, so it is not used.
- Each run's `meta.json` records `l9_available` and the configuration. A
  unit test runs a `baseline` run and asserts that no prompt contains L9
  text, the forge tool is never bound, and no `accord_*` or `concord_*`
  message exists. With the switch off, a second test asserts the same for
  the skills directory (never read).
- Separate images or deployments for plain and L9 were rejected as the main
  mechanism, because environment differences would confound the comparison.

## Risks / Trade-offs

- [The silent failure may not occur reliably, because the confirm round
  lets each party check the plan against its own data, which can surface
  the failure.] Mitigation: task 4.3b probes the baseline against the real
  model before the L9 bridge is built, and reports silent and surfaced
  counts. The role prompts carry no guardrail lines (removed by user
  decision of 2026-10-27), so the probe measures an unguarded baseline. If
  the failure is still rare, the options are to accept the observed rate or
  to add a guarded prompt variant, identical in every configuration. That
  decision is the user's and is made after the probe, not before.
  **Updated 2026-10-27 (user): the silent baseline failure is the aim, so
  "accept the observed rate" is not the path.** When the baseline does not
  fail silently, the scenario is refined until it does (task 4.3c).
- [Refining the scenario until the baseline fails makes the comparison
  unfair.] Mitigation: refine on `baseline` only, and never look at an L9
  run to decide a refinement. Log every refinement (what changed, why, the
  probe counts before and after) in the decisions file and give each
  scenario version a number that goes into `meta.json`. Freeze the version
  before the first L9 run, and run `baseline` and `l9_hybrid` on that same
  version. Every refinement keeps the case realistic and keeps a correct
  answer available: a feasible plan must still exist where the checker says
  so, and nothing the L9 protocols would need to detect the problem is
  removed from any party's own data. If a refinement would only work by
  hiding information from every agent, it is not used.
- [The result is cherry-picked.] Mitigation: runs are counted, every run
  directory is kept, and the summary reports silent, surfaced, passed and
  invalid counts per configuration, not one chosen run.
- [The L9 run does not prevent the failure.] The upstream CLARIFY phase
  returns an empty ambiguity list, so a flagged "delivery" stays flagged
  (D5). Not preventing it is a valid finding and is reported as such, not
  patched.
- [Hub-and-spoke delivery is less literal than one shared channel.]
  Mitigation: every step still runs in a SLIM group session, the moderator
  relays the public transcript, and the transcript records sender and
  addressees per message (D3).
- [Long runs.] Mitigation: an overall `SUPPLY_CHAIN_RUN_TIMEOUT` (default
  900 s) enforced by the run loop, a per-step broadcast timeout, and
  per-LLM-call timeouts. A timeout ends the run with status `withheld` and
  reason `timeout`, and the checker marks it `INVALID` (D8).
- [Scaffolding bias: the moderator's turn order or confirm step could
  prevent a failure that would otherwise happen.] Mitigation: both
  configurations use the identical scaffold, so the comparison stays fair.
  Every run file records the scaffold version.
- [LLM nondeterminism makes a single run anecdotal.] Mitigation: save every
  run with its model and parameters. Batch statistics are out of scope.
- [The receiver LLM fails to call forge, or prepends prose.] Mitigation:
  this is protocol behavior, so we handle it with the skill's own reject and
  retry rules and record it, not patch it.
- [The vendored text drifts from upstream through edits or formatters.]
  Mitigation: the checksum test, the dash exclusion, and adding the
  directory to formatter excludes if any formatter touches it.
- [The licence of the vendored code.] Mitigation: the work stays local and
  is never pushed (user decision of 2026-10-27).
- [Cost.] Mitigation: limits are set by environment variables, and the
  suggested prompts make the selected configuration explicit.

## Migration Plan

The change is additive: it adds a new profile, new charts and a new catalog
entry. The logistics workflow and its UI must stay unchanged. Their existing
tests are the regression guard for the shared store and feed changes.
Rollback means removing the profile, the catalog entry and the charts. No
data migration is needed.

## Open Questions

- Should the moderator randomize the baseline turn order? This is deferred
  to the batch-experiment change. The order is fixed for now and recorded.
