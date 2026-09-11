# IoC pattern mock implementations  - Assessment from Lungo reference library

## Constraints (all patterns)

| Rule | Meaning |
| --- | --- |
| Mock store only | A Lungo-owned in-memory store (in-process module or the shared mock sidecar below). Never CFN `:9000` / `:9002` / `:8089`, never `ioc-cfn-mas-client-lib`. |
| Structured records | Facts have keys, actor, timestamp, and a scope id (`order_id`, `session_id`, `intent://…@vN`). Not a blob of chat log. |
| Seed data is demo data | Seeds are coffee-domain fixtures only. No credentials, tokens, or API keys in mock stores, seed files, or docs. Any endpoint/port the mock needs comes from `config/config.py` env vars. |
| Topology | Catalog `starting_topology` must show the extra cognitive node (memory / store / buffer / ledger / registry / poll / aligner) plus the agents that read/write it. |
| Runnable in UI | Set `chat_api_target` (`exchange` / `logistics` / `discovery`) so the LHS is not docs-only. Suggested prompts must drive the demo. |
| Contrast is the product | The demo fails if a reviewer cannot tell "without pattern" from "with mock". Prefer two prompts or a flag, not a unique happy-path that already works via messages. |
| Do not steal other categories | Event ledger is **not** OTel/OXP. Team formation is **not** Recruiter ranking. Intent registry is **not** policy enforcement. Alignment is **not** group chat. |

## Mock architecture: pick a tier first

Lungo agents are **separate processes** (`docker compose`: supervisors, farms, shipper, accountant, helpdesk). A module-level `dict` is shared only inside one process, so the tier decides whether a pattern is a one-file change or needs a service.

**Tier A — in-process module.** All readers and writers live in one process (a supervisor and its graph nodes). Implement as a module under `common/ioc_mocks/`, no new container.

**Tier B — shared mock sidecar.** Writers and readers are in different containers. Implement one small FastAPI service (in-memory dict, no DB) plus a thin HTTP client in `common/ioc_mocks/client.py`, added to `docker-compose.yaml` under a **new** profile (e.g. `ioc-mock`) that must not be confused with the existing `ioc` CFN profile.

| Pattern | Tier | Why |
| --- | --- | --- |
| Shared Agent Memory | B | Buyer, farm, shipper, accountant all retain |
| Event Ledger | B | Multiple agents append |
| Shared Intent Registry | B | Supervisor publishes, farm/shipper/finance read |
| Shared Knowledge Store | A + read-only seed (B only if mock ingest writes) | Reads dominate; a mounted seed file is enough for v1 |
| Session Context Buffer | A for v1 (B if farms write) | Keep writers in the auction supervisor first |
| Team Formation via Polling | A for v1 | Scripted candidates inside the coordinator |
| Mediated Semantic Alignment | A | Referee and orchestrator both live in the supervisor |

Build Tier B **once**, for the first pattern that needs it, and reuse it: one service with per-pattern route groups beats four sidecars.

## Shared mocking rules

**Code shape to copy.** `agents/logistics/helpdesk/store/{event,base,memory}.py` is the existing precedent: a Pydantic record, an `abc` store interface, an async in-memory implementation with a lock. Copy that shape. Note that the helpdesk store itself is the **anti-example** for Shared Agent Memory (it is private and parses chat lines via `parse_order_event_line`); reuse the code structure, not the sourcing.

**Scope every record.** Key by workflow instance plus business id. `common/workflow_context_prop.read_workflow_context()` already returns `workflow_name` and `instance_id` from OTel baggage and crosses A2A hops, so the mock can scope records without new parameters on every function.

**One env flag per pattern.** Follow `config/config.py` style (`EMIT_WORKFLOW_EVENTS`), e.g. `MOCK_SHARED_MEMORY`. Default **off** so the baseline is what main already does, and the flag is the baseline switch used in demos and tests.

**Keep the mock dumb on purpose.** No persistence, no migrations, no auth, no eviction beyond the pattern's own TTL. Restarting the service may lose state; say so in the pattern doc instead of engineering around it.

**Be honest about what is mocked.** Each pattern below lists *must be honest* (the part the pattern is actually demonstrating) and *may be faked* (anything a real IoC product would own). A mock that fakes the honest part demonstrates nothing.

**Inject time and ids.** TTLs, versions, and sequence numbers must be injectable so tests are deterministic and do not sleep.

**Inspect route.** Every mock exposes a read-only dump (`GET`) scoped to the run, used by the demo, screenshots, and tests.

## What "done" looks like (shared acceptance)

- [ ] Catalog row: non-empty `starting_topology`, `use_case` / `scenario` not `---`, `chat_api_target` set, `supports_sse` / `supports_streaming` honest.
- [ ] Workflow markdown **Workflow** section matches the running graph (replace "once a concrete layout exists" where still present).
- [ ] Mock store module (or sidecar route group) with the record, operations, and inspect dump described in the pattern section.
- [ ] Env flag off by default; with the flag off the workflow behaves exactly as it does on `main`.
- [ ] One **baseline** path and one **pattern** path; documented prompts for both.
- [ ] At least one **follow-up prompt** that would fail or lie without the store.
- [ ] Unit tests for the store operations **without** LLM (table-driven), plus one supervisor-level test that the follow-up reads the store.
- [ ] No dependency on `COMPOSE_PROFILES` containing `ioc`.

Existing live overlays you may reuse (do not rebuild farms from scratch unless the pattern needs it):

| Overlay | `chat_api_target` | Supervisors / agents |
| --- | --- | --- |
| Auction / farms | `exchange` | Auction supervisor, Brazil / Colombia / Vietnam farms |
| Logistics group | `logistics` | Logistics supervisor, Tatooine farm, shipper, accountant, SLIM group |
| Recruiter / directory | `discovery` | Recruiter supervisor, on-demand agents |

---

## Pattern 1 — Shared Agent Memory

**Library:** `docs/workflows/shared_agent_memory.md`
**Catalog name:** Shared Agent Memory
**Also in:** `ioc-app-mas-patterns` as `shared-agent-memory` (Proposed, no implementation link)
**Ticket:** [coffeeAgntcy#710](https://github.com/agntcy/coffeeAgntcy/issues/710)
**Overlay:** Logistics Group Messaging (`logistics`) — keep SLIM, add a Memory node beside Transport
**Tier:** B (sidecar)

### What it is

A scoped working blackboard. Agents **retain** operational facts (order id, state, quantity, payment flag) and **recall** them by key. Messages still carry dialogue; memory holds what the group knows.

### What to mock

| Real component (out of scope) | Mocked as | Lives in |
| --- | --- | --- |
| Managed shared-memory service | FastAPI sidecar, dict keyed by scope | `mock_ioc_store/` service + compose `ioc-mock` profile |
| Client SDK | `retain` / `recall` helpers over HTTP | `common/ioc_mocks/shared_memory.py` |
| Semantic recall ("what constraints are open?") | Exact key match, then optional substring filter | same module |
| Durability, replication, retention policy | Nothing — process lifetime only | — |

### How to mock it

Record and operations:

```python
class MemoryFact(BaseModel):
    scope_id: str        # f"{instance_id}:{order_id}"
    key: str             # "state", "quantity_lbs", "price_per_lb", "farm"
    value: str | float | bool
    actor: str           # "shipper_agent"
    recorded_at: datetime


async def retain(scope_id: str, facts: Sequence[MemoryFact]) -> None: ...
async def recall(scope_id: str, keys: Sequence[str] | None = None) -> list[MemoryFact]: ...
async def dump(scope_id: str) -> list[MemoryFact]: ...
```

Call sites — one `retain` per existing transition in `common/logistics_states.py::LogisticsStatus`, so no new graph nodes are needed:

- `RECEIVED_ORDER` — logistics supervisor, after `CreateOrderArgs` is resolved: order id, quantity, price, farm.
- `HANDOVER_TO_SHIPPER` — `agents/logistics/farm/agent.py`.
- `CUSTOMS_CLEARANCE` and `DELIVERED` — `agents/logistics/shipper/agent.py`.
- `PAYMENT_COMPLETE` — `agents/logistics/accountant/agent.py`.
- `recall` before the shipper publishes `DELIVERED` (payment gate) and in the supervisor when answering a user follow-up.

Must be honest:

- Writes are **structured fields**, produced by the agent that owns the transition — never by parsing message text. If a developer reaches for `extract_status()` on a transcript to fill memory, the demo is dead.
- Reads are **by key**, and the answer text must come from the recalled fact, not from the model restating chat.
- Every fact carries `actor` and `recorded_at`, so the dump shows who knew what.

May be faked: transport (plain HTTP), storage (dict), auth (none), "recall by intent" (keys plus substring), eviction (none).

Must not: mirror the SLIM transcript into memory; replace the helpdesk store; require the `ioc` profile.

### Inspect and baseline

`GET /mock-ioc/memory/{scope_id}` returns the fact list. `MOCK_SHARED_MEMORY=false` (default) skips all retain/recall calls, leaving the current behavior untouched.

### Demo prompts

1. Place the Tatooine 5,000 lb order (existing group-messaging prompt).
2. Follow-up in a **new** request: "Has payment cleared for this order?"
3. Baseline: same follow-up with the flag off.

### Without vs with

Without, every hop repeats order id, quantity, and price, and the follow-up depends on whatever text is still in context. With, each transition writes one fact and the follow-up answers from `{ order_id, state: PAYMENT_COMPLETE }`.

### Effort / risks

**Effort: M (best first pick).** Agents and transitions already exist; the sidecar is the only new moving part and later patterns reuse it. Risk: looking like "we logged the chat" — mitigate by recalling structured fields and showing the dump.

One developer: sidecar + client module + four retain call sites + one recall + catalog + docs + tests.

---

## Pattern 2 — Session Context Buffer

**Library:** `docs/workflows/session_context_buffer.md`
**Catalog name:** Session Context Buffer
**Overlay:** Auction (`exchange`), origin negotiation — not logistics delivery
**Tier:** A for v1 (writers inside the auction supervisor), B if farms write directly

### What it is

A temporary shared scratchpad for one live deal: bid floor, last counter, payment constraint. Authoritative while the deal lives, disposable when it closes.

### What to mock

| Real component (out of scope) | Mocked as | Lives in |
| --- | --- | --- |
| Session store with TTL | Dict `session_id → SessionBuffer` | `common/ioc_mocks/session_buffer.py` |
| Field ownership / permissions | `owner` per field, rejected write returns an error | same module |
| Expiry daemon | TTL checked on read/write against an injected clock | same module |
| Distributed locking, replication | Nothing — one asyncio lock | — |

### How to mock it

```python
class BufferField(BaseModel):
    name: str            # "floor", "last_counter", "payment_terms"
    value: str | float
    owner: str           # only this actor may overwrite
    updated_at: datetime


class SessionBuffer(BaseModel):
    session_id: str
    fields: dict[str, BufferField]
    expires_at: datetime
    retired: bool = False


async def put_field(session_id: str, field: BufferField) -> None: ...
async def snapshot(session_id: str) -> SessionBuffer | None: ...
async def retire(session_id: str) -> None: ...
```

Call sites: auction supervisor graph nodes around the bid/counter exchange. Mint `session_id` from the workflow instance id so the buffer is per run.

Must be honest:

- **Ephemerality.** After `retire()` or TTL expiry, `snapshot()` returns nothing and the agent must say it has no current state. If the buffer outlives the deal, this is Shared Agent Memory wearing a different hat.
- **Ownership.** A non-owner write is rejected, and the rejection is visible in the demo (log line or error text).
- **Shared read.** At least two distinct actors read the same field; a buffer only one agent ever touches proves nothing.

May be faked: which agent plays finance, the negotiation itself (scripted counters are fine), storage, TTL length (seconds is fine for a demo — expose it as config).

Must not: keep fulfillment state such as `PAYMENT_COMPLETE` after close; share a store instance with the Shared Agent Memory mock.

### Inspect and baseline

`GET /mock-ioc/session/{session_id}` returns the snapshot including `expires_at` and `retired`. `MOCK_SESSION_BUFFER=false` disables writes and snapshot reads.

### Demo prompts

1. Start a Colombia price negotiation.
2. "What is the current floor and last counter on this session?"
3. After close (or TTL), ask again — the snapshot is gone; the baseline still improvises from leftover chat.

### Without vs with

Without, floor and counter exist only in each agent's prompt window and a closed deal leaves stale numbers around. With, all parties read one `session://…` object that is explicitly retired.

### Effort / risks

**Effort: M.** The clock and the close moment are the design work, not the store. Risk: collapsing into Shared Agent Memory — the TTL and `retired` flag are what keep it separate, so make them visible.

---

## Pattern 3 — Shared Knowledge Store

**Library:** `docs/workflows/shared_knowledge_store.md`
**Catalog name:** Shared Knowledge Store
**Overlay:** Auction (`exchange`) — planning and "what did we pay last season?" prompts
**Tier:** A plus a read-only seed file; B only if the mock ingest path writes

### What it is

Curated, versioned, cross-task records (yield history, settled prices, partner reliability) that agents **cite by id** instead of recalling from a prompt.

### What to mock

| Real component (out of scope) | Mocked as | Lives in |
| --- | --- | --- |
| Governed catalog / RAG backend | Seed JSON of ~10 records | `common/ioc_mocks/knowledge_seed.json` |
| Record resolver | `get(record_id)` with `@vN` parsing | `common/ioc_mocks/knowledge_store.py` |
| Curated ingestion pipeline | `ingest()` that appends a new version with `source` | same module |
| Search / embeddings | Exact id lookup plus a small name index | same module |

### How to mock it

```python
class KnowledgeRecord(BaseModel):
    record_id: str       # "knowledge://origin/colombia/yield-history"
    version: int
    as_of: date
    source: str          # "seed:2026-harvest-report"
    payload: dict[str, str | float]


def get(record_id: str, version: int | None = None) -> KnowledgeRecord | None: ...
def history(record_id: str) -> list[KnowledgeRecord]: ...
def ingest(record_id: str, payload: dict, source: str) -> KnowledgeRecord: ...
```

Call sites: an auction supervisor tool that resolves a record and returns it to the graph. The user-visible answer must include `record_id@vN`.

Must be honest:

- **Citation.** The agent's answer names the record id and version. Without the citation this is just another inventory tool.
- **Stability.** Two runs of the same prompt cite the same id and the same numbers; no paraphrasing the payload into different figures.
- **Provenance and versioning.** `source` and `as_of` are shown, and `ingest()` produces `@v(n+1)` while `@vn` stays readable.

May be faked: the data itself, the ingest trigger (an HTTP poke is fine), any notion of access control or approval workflow.

Must not: duplicate the farms' live inventory tools (this is history and settled prices, not current stock); silently overwrite a version in place.

### Inspect and baseline

`GET /mock-ioc/knowledge/{record_id}` returns the version history. `MOCK_KNOWLEDGE_STORE=false` falls back to today's answer path.

### Demo prompts

1. "What yield history do we have on record for Colombia? Cite the record."
2. Baseline: the same question answers with numbers and no id.
3. Optional: run the mock ingest, ask again, see `@v4`.

### Without vs with

Without, each run paraphrases whatever the model or the local tool produced. With, answers cite `knowledge://…@vN` with a source and date, and the cited record is reproducible.

### Effort / risks

**Effort: S–M.** Smallest mock here. Risk: the weakest demo of the seven, because it can look like a lookup table — the version bump and citation are what make it a pattern.

---

## Pattern 4 — Event Ledger (Episodic Memory)

**Library:** `docs/workflows/event_ledger_episodic_memory.md`
**Catalog name:** Event Ledger (Episodic Memory)
**Overlay:** Logistics (the doc's shipment-failure story) or auction
**Tier:** B (several agents append)

### What it is

An append-only, ordered history of decisions, tool calls, and checks, bound to a business object, so a reviewer can replay what happened. For operators — not the store agents query to pick the next hop.

### What to mock

| Real component (out of scope) | Mocked as | Lives in |
| --- | --- | --- |
| Event-sourcing backend | Append-only list per `order_id` | sidecar route group + `common/ioc_mocks/event_ledger.py` |
| Sequence / ordering guarantees | Monotonic `seq` assigned by the sidecar under a lock | sidecar |
| Replay tooling | `GET` returns the ordered list; supervisor renders it | supervisor tool |
| Retention, compaction, signing | Nothing | — |

### How to mock it

```python
class LedgerEntry(BaseModel):
    seq: int             # assigned server-side, never by the caller
    order_id: str
    kind: str            # "decision" | "tool_call" | "check" | "failure"
    actor: str
    summary: str
    payload: dict[str, str]
    recorded_at: datetime


async def append(order_id: str, entry: LedgerEntry) -> int: ...
async def replay(order_id: str) -> list[LedgerEntry]: ...
```

Call sites: three or four points that already exist — supervisor order decision, a farm or MCP tool call, the payment check, and an injected customs failure.

Must be honest:

- **Append-only and ordered.** No update, no delete; `seq` comes from the store, not the caller, and replay returns insertion order even with concurrent writers.
- **Business correlation.** Entries key on `order_id`, not on `trace_id`. If a developer needs OTel to make replay work, the pattern has drifted into Observability.
- **Reasoning steps, not transport chatter.** A `decision` entry says what was chosen and why in one line; do not log every message frame.

May be faked: the failure (inject it), payload depth, storage, any signing or tamper-evidence.

Must not: read from `default.otel_traces`, the OTLP collector, or OXP; duplicate the `event_v1` workflow-instance store used by the live topology API.

### Inspect and baseline

`GET /mock-ioc/ledger/{order_id}` returns the ordered entries. `MOCK_EVENT_LEDGER=false` disables appends and the replay tool.

### Demo prompts

1. Run an order until the injected customs failure.
2. "Replay the decision timeline for this order."
3. Baseline: the supervisor can only restate its last message.

### Without vs with

Without, the post-mortem is a chat summary. With, the reviewer walks ordered entries and can point at the step that introduced the bad assumption.

### Effort / risks

**Effort: M.** Risk: being read as a duplicate of Observe/OXP work — the acceptance check is that the ledger has no `trace_id` dependency and no collector.

---

## Pattern 5 — Shared Intent Registry

**Library:** `docs/workflows/shared_intent_registry.md`
**Catalog name:** Shared Intent Registry (placeholder catalog from [#750](https://github.com/agntcy/coffeeAgntcy/pull/750))
**Overlay:** Logistics order chain
**Tier:** B (supervisor publishes, other containers read)

### What it is

The canonical, versioned statement of goal and constraints. Leadership publishes and supersedes; participants query a snapshot before acting. It does not negotiate meaning — that is alignment.

### What to mock

| Real component (out of scope) | Mocked as | Lives in |
| --- | --- | --- |
| Intent service with subscriptions | Dict `intent_id → [IntentVersion]`, readers poll on read | sidecar + `common/ioc_mocks/intent_registry.py` |
| Push notification to subscribers | Agents call `snapshot()` before each major action | call sites |
| Publisher authorization | One allowed publisher id, hard-coded constant | same module |
| Acknowledgement trail | Optional `ack(actor, version)` list | same module |

### How to mock it

```python
class IntentVersion(BaseModel):
    intent_id: str       # "intent://order-8842"
    version: int
    goal: str
    constraints: dict[str, str | float | bool]   # price_cap, organic, deliver_by
    published_by: str
    effective_at: datetime
    superseded: bool = False


async def publish(intent_id: str, goal: str, constraints: dict, publisher: str) -> IntentVersion: ...
async def snapshot(intent_id: str) -> IntentVersion | None: ...   # latest non-superseded
async def ack(intent_id: str, version: int, actor: str) -> None: ...
```

Call sites: supervisor publishes v1 when the order opens and supersedes to v2 when the user changes the ask mid-run; farm and shipper call `snapshot()` before planning and include `@vN` in their reply.

Must be honest:

- **Versioning and supersession.** v2 does not delete v1; `snapshot()` returns v2 and history still shows v1. Agents must name the version they acted on.
- **Mid-run change.** The demo's whole point is that a constraint changes **after** work started and downstream agents pick it up without being re-prompted with the full history.
- **Single publisher.** A non-publisher write is rejected; goals do not drift in from participants.

May be faked: push/subscribe (polling on read is fine), constraint semantics (nobody has to enforce the price cap — that is Policy-Enforced Execution), storage.

Must not: implement enforcement or blocking; become a second system prompt (if the constraint only reaches agents through prompt text, nothing was demonstrated).

### Inspect and baseline

`GET /mock-ioc/intent/{intent_id}` returns all versions with `superseded` flags and acks. `MOCK_INTENT_REGISTRY=false` restores today's single-prompt behavior.

### Demo prompts

1. Place the order with organic certification and March 15 delivery.
2. "Move delivery to March 10."
3. "Which intent version is the shipper working from?"
4. Baseline: the shipper keeps planning March 15.

### Without vs with

Without, a constraint change lives in one message and other agents never see it. With, every participant reads `intent://order-…@v2` and says so.

### Effort / risks

**Effort: M.** The supersede moment needs a real mid-run hook. Risk: indistinguishable from prompt engineering unless version ids appear in answers and in the dump.

---

## Pattern 6 — Team Formation via Polling

**Library:** `docs/workflows/team_formation_via_polling.md`
**Catalog name:** Team Formation via Polling (placeholder from #750)
**Overlay:** Logistics rush order, or a thin new coordinator — **not** the Recruiter overlay
**Tier:** A for v1 (scripted candidates in the coordinator), B when real agents answer

### What it is

A coordinator opens a poll (roles, constraints, deadline); candidates accept or decline; the poll closes into a queryable roster that later work cites. The artifact is membership, not ranking.

### What to mock

| Real component (out of scope) | Mocked as | Lives in |
| --- | --- | --- |
| Poll engine with deadlines and quorum | `Poll` object with an injected clock | `common/ioc_mocks/team_poll.py` |
| Candidate agents replying over transport | Scripted responders (one declines, one is silent) | fixture module |
| Capability discovery | Static candidate list with role tags | same module |
| Identity / commitment binding | `team_id` string plus role → agent id map | same module |

### How to mock it

```python
class PollResponse(BaseModel):
    actor: str
    role: str
    accepted: bool
    terms: dict[str, str] | None = None


class TeamRoster(BaseModel):
    team_id: str         # "team://order-8842"
    bindings: dict[str, str]        # role -> agent id
    declined: list[str]
    unfilled: list[str]
    closed_at: datetime
    partial: bool


async def open_poll(team_id: str, roles: Sequence[str], constraints: dict, deadline: datetime) -> None: ...
async def respond(team_id: str, response: PollResponse) -> None: ...
async def close_poll(team_id: str) -> TeamRoster: ...
async def roster(team_id: str) -> TeamRoster | None: ...
```

Must be honest:

- **Commitment, not ranking.** Membership comes from an explicit accept. No scoring, no OASF similarity — that is Recruiter, a Discovery-category pattern.
- **Deadline and partial close.** At least one role must go unfilled or arrive late in a demo run, and the roster records `unfilled` / `partial` rather than pretending.
- **The roster is queryable afterwards.** Later steps cite `team://…`, and a reviewer can ask who declined.

May be faked: candidate reasoning (scripted accept/decline is fine), invitations (direct calls), the directory, the clock.

Must not: rank candidates; reuse the recruiter's discovery flow as the poll; treat the group-chat membership list as the roster.

### Inspect and baseline

`GET /mock-ioc/team/{team_id}` returns bindings, declines, and unfilled roles. `MOCK_TEAM_POLL=false` restores sequential ad-hoc messaging.

### Demo prompts

1. "Form a team for a Tatooine cold-chain rush order."
2. "Who is on the team and who declined?"
3. Baseline: three separate chats and no roster object.

### Without vs with

Without, membership exists only in message history and a restart loses it. With, one roster object binds roles to agents before execution and every later step cites the same team id.

### Effort / risks

**Effort: M–L.** The lifecycle (open, respond, deadline, close) is more state than the other mocks. Risk: reimplementing Recruiter — keep accept/decline and the roster as the only cognitive artifact.

---

## Pattern 7 — Mediated Semantic Alignment

**Library:** `docs/workflows/mediated_semantic_alignment.md`
**Catalog name:** Mediated Semantic Alignment (placeholder from #750)
**Related (real CFN, out of scope here):** [coffeeAgntcy#701](https://github.com/agntcy/coffeeAgntcy/issues/701)
**Overlay:** Auction plus Brazil and Colombia (`exchange`)
**Tier:** A (referee and orchestrator both in the supervisor process)

### What it is

A caller-mediated offer loop. A referee turns a goal into an agenda of issues and options and scores each round, but never calls the agents; an orchestrator dispatches `propose` / `respond` over A2A and posts replies back. Terminal states: `agreed`, `broken`, `timeout`.

### What to mock

| Real component (out of scope) | Mocked as | Lives in |
| --- | --- | --- |
| CFN SAO engine (`:8089`) and SSTP | Local referee module, clearly named `MockSemanticAlignmentReferee` | `common/ioc_mocks/alignment_referee.py` |
| Intent discovery / options generation | Hard-coded agenda: `price_band`, `grade`, `unit` | same module |
| Scoring and offer snapping | Nearest-option snap plus a fixed coherence number | same module |
| `ioc-cfn-mas-client-lib` SDK | Direct function calls: `start()` / `decide()` | orchestrator module |
| Workspace / MAS registration on `:9000` | Nothing — participants are the existing farm ids | — |

### How to mock it

```python
class AlignmentMessage(BaseModel):
    participant_id: str        # "brazil" | "colombia" (farm_registry slugs)
    action: str                # "propose" | "respond"
    allowed_actions: list[str]
    current_offer: dict[str, str]
    issues: dict[str, list[str]]   # issue -> options


class AlignmentReply(BaseModel):
    participant_id: str
    action: str                # "accept" | "reject" | "counter_offer"
    offer: dict[str, str] | None = None
    reason: str | None = None


def start(session_id: str, participants: Sequence[str], goal: str, max_rounds: int) -> list[AlignmentMessage]: ...
def decide(session_id: str, replies: Sequence[AlignmentReply]) -> AlignmentRound: ...
```

Farms parse the JSON negotiate payload and answer with an action plus one of the offered options. A scripted decision table is acceptable for v1; an LLM choice is fine as long as it can only pick from `issues`.

Must be honest:

- **Caller mediation.** The referee never calls a farm. If the referee reaches into A2A, the pattern's defining property is gone.
- **Structured offers only.** Farms reveal an action and a chosen option, never their private reasoning. `reason` is display text, not an input to scoring.
- **Rotating roles and a terminal state.** One proposer per round, roles alternate, and the loop ends in `agreed` / `broken` / `timeout` with one option per issue.
- **A2A payload shape follows the library doc**, so a later swap to the real engine is a referee replacement, not a rewrite.

May be faked: issue and option discovery (hard-coded), scores (fixed numbers), round count (2–4), participant economics (a small per-farm utility table).

Must not: call CFN or install the client lib; present mock scores as real alignment metrics; let the loop reduce to free-form chat.

### Inspect and baseline

`GET /mock-ioc/alignment/{session_id}` returns the agenda, each round's messages and replies, and the final agreement. `MOCK_ALIGNMENT=false` leaves the auction as is.

### Demo prompts

1. "Align Brazil and Colombia on a USD/lb price band and grade."
2. Show the agenda, the round dump, and the final agreement.
3. Baseline: "agree on a price" as free-form chat, with no agenda object.

### Without vs with

Without, farms exchange "a fair price" and "the usual grade" with no proof they meant the same thing. With, an explicit agenda of issues and options produces one chosen option per issue.

### Effort / risks

**Effort: L.** Round loop, two farms, and a JSON protocol. Risk: confusion with the real CFN epic — label the referee `MOCK` in code, logs, and UI, and keep #701 explicitly out of scope.

---

## Comparison

| Pattern | Overlay | Tier | Core mocked artifact | Mock complexity | Collides with | Order |
| --- | --- | --- | --- | --- | --- | --- |
| Shared Agent Memory | Logistics | B | Fact store (retain/recall by key) | Low | Chat log as "memory" | **1 — start here** |
| Session Context Buffer | Auction | A | TTL scratchpad with field owners | Low–mid | Shared Agent Memory | 2 |
| Shared Intent Registry | Logistics | B | Versioned goal + constraints | Mid | System prompt | 2–3 |
| Shared Knowledge Store | Auction | A + seed | Cited, versioned records | Low | Farm inventory tools | 3 |
| Event Ledger | Logistics or auction | B | Append-only ordered entries | Mid | OTel / OXP | 3 |
| Team Formation via Polling | Logistics (not Recruiter) | A | Roster with declines and unfilled roles | Mid–high | Recruiter | 4 |
| Mediated Semantic Alignment | Auction + 2 farms | A | Agenda + terminal agreement | High | CFN #701 | 4–5 |
