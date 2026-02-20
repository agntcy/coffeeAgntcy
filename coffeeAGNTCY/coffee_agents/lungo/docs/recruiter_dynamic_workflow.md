# Recruiter Supervisor — Dynamic Workflow

The Recruiter Supervisor is an ADK-based agent that discovers agents from the AGNTCY directory, evaluates them, and delegates tasks to them at runtime. It runs as a FastAPI service on port `8882` and communicates with a remote Recruiter Service (port `8881`) via the A2A protocol.

---

## Architecture

```
User Request (HTTP)
    │
    ▼
┌──────────────────────────────────────────────────────┐
│  main.py — FastAPI server (:8882)                    │
│  POST /agent/prompt        (single response)         │
│  POST /agent/prompt/stream (NDJSON streaming)        │
│  GET  /.well-known/agent-card.json                   │
│  GET  /health  ·  GET /v1/health                     │
└──────────────┬───────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│  agent.py — Root Supervisor (ADK LlmAgent)           │
│  Name: "recruiter_supervisor"                        │
│  Model: LiteLlm (configurable via LLM_MODEL)        │
│                                                      │
│  Tools:                                              │
│    recruit_agents()    → recruiter_client.py          │
│    evaluate_agent()    → recruiter_client.py          │
│    select_agent()                                    │
│    deselect_agent()                                  │
│    send_to_agent()                                   │
│    clear_recruited_agents()                           │
│                                                      │
│  Sub-agent:                                          │
│    dynamic_workflow (DynamicWorkflowAgent)            │
└──────────┬──────────────────┬────────────────────────┘
           │                  │
           │ recruit/evaluate │ delegate task
           ▼                  ▼
┌─────────────────┐  ┌────────────────────────────────┐
│ Recruiter Svc   │  │ dynamic_workflow_agent.py       │
│ (A2A :8881)     │  │ Sends A2A message to the       │
│ agent discovery │  │ selected remote agent           │
│ & evaluation    │  └────────────────────────────────┘
└─────────────────┘
```

---

## Files

| File | Purpose |
|---|---|
| `main.py` | FastAPI application. HTTP endpoints, NDJSON streaming, health checks, CORS. |
| `agent.py` | Root supervisor agent definition, tool functions, session management, `call_agent()` / `stream_agent()` entry points. |
| `dynamic_workflow_agent.py` | `DynamicWorkflowAgent` (extends `BaseAgent`). Reads selected agent from session state and sends it an A2A message. |
| `recruiter_client.py` | `recruit_agents()` and `evaluate_agent()` ADK tool functions. Streams A2A requests to the remote Recruiter Service. |
| `models.py` | Pydantic models (`AgentRecord`, `RecruitmentResponse`) and session state key constants. |
| `shared.py` | Singleton `AgntcyFactory` accessor for creating A2A transports/clients. |
| `card.py` | A2A `AgentCard` for this supervisor (served at `/.well-known/agent-card.json`). |
| `recruiter_service_card.py` | A2A `AgentCard` for the remote Recruiter Service (URL from `RECRUITER_AGENT_URL` env var, default `localhost:8881`). |

---

## Session State

All inter-component communication happens through ADK session state. These keys are defined in `models.py`:

| Key | Type | Description |
|---|---|---|
| `recruited_agents` | `dict[str, dict]` | Agent records keyed by CID. Accumulated across searches (merged, not replaced). |
| `evaluation_results` | `dict[str, dict]` | Evaluation results keyed by agent ID. Accumulated across evaluations. |
| `selected_agent` | `str \| None` | CID of the agent currently selected for conversation. |
| `task_message` | `str \| None` | Message to forward to the selected agent. Set by `send_to_agent()`, consumed and cleared by `DynamicWorkflowAgent`. |

---

## Workflow

The root supervisor uses an LLM-driven instruction prompt to decide which tool to call based on the user's intent:

### 1. Search / Recruit
User says *"find me an agent for shipping"*

→ LLM calls `recruit_agents(query)` → streams an A2A request to the Recruiter Service → parses `DataPart` responses with `metadata.type == "found_agent_records"` → merges results into `recruited_agents` state → returns a human-readable summary.

### 2. Evaluate
User says *"evaluate the Shipping agent against edge cases"*

→ LLM calls `evaluate_agent(agent_identifier, query)` → resolves the agent by name or CID from state → sends the single agent record + evaluation criteria to the Recruiter Service → the service delegates to its `agent_evaluator` sub-agent → results come back with pass/fail per scenario → merged into `evaluation_results` state.

### 3. Select
User says *"select the Shipping agent"*

→ LLM calls `select_agent(agent_identifier)` → looks up by name (case-insensitive, partial match) or CID → sets `selected_agent` state.

### 4. Send Message (Delegate)
User sends any message while an agent is selected

→ LLM calls `send_to_agent(message)` → sets `task_message` state → LLM transfers to `dynamic_workflow` sub-agent → `DynamicWorkflowAgent._run_async_impl()` reads `selected_agent` + `task_message` + `recruited_agents` from state → creates an A2A client via `AgntcyFactory` → sends the message → yields the response as an ADK `Event` → clears `task_message`.

### 5. Deselect
User says *"go back"* or *"deselect"*

→ LLM calls `deselect_agent()` → clears `selected_agent` state → user is back in supervisor mode.

### 6. Clear
User says *"clear all agents"*

→ LLM calls `clear_recruited_agents()` → resets `recruited_agents` to `{}`.

---

## Streaming

The `/agent/prompt/stream` endpoint returns NDJSON. It merges two concurrent event sources:

1. **ADK events** — from the LlmAgent runner (tool calls, status updates, final response).
2. **A2A side-channel events** — pushed onto a module-level `asyncio.Queue` in `recruiter_client.py` during `recruit_agents()` / `evaluate_agent()` tool execution, since ADK blocks while tools run.

Both producers push dicts onto a merged queue; the consumer serialises them as newline-delimited JSON. Each line has this shape:

```json
{
  "response": {
    "event_type": "status_update | completed | error",
    "message": "...",
    "state": "working | completed",
    "author": "recruiter_supervisor | recruiter_service | ...",
    "agent_records": {},
    "evaluation_results": {},
    "selected_agent": { "cid": "...", "name": "...", "description": "..." }
  },
  "session_id": "..."
}
```

`agent_records`, `evaluation_results`, and `selected_agent` are only present on `completed` events.

---

## Data Models

### `AgentRecord`
```python
class AgentRecord(BaseModel):
    cid: str
    name: str
    description: str = ""
    url: str = ""
    version: str = "1.0.0"
    skills: list[dict] = []
```

Key methods:
- `to_agent_card()` — converts to an `a2a.types.AgentCard` for A2A communication.
- `to_safe_agent_name()` — sanitises the name into a valid Python identifier (required by ADK's `BaseAgent`).

### `RecruitmentResponse`
```python
class RecruitmentResponse(BaseModel):
    text: Optional[str] = None
    agent_records: dict[str, dict] = {}
    evaluation_results: dict[str, dict] = {}
```

Parsed from A2A message parts. `TextPart` → `text`, `DataPart` with `metadata.type == "found_agent_records"` → `agent_records`, `DataPart` with `metadata.type == "evaluation_results"` → `evaluation_results`.

---

## DynamicWorkflowAgent

A custom `BaseAgent` subclass (not LLM-driven). It implements `_run_async_impl()` directly:

1. Reads `selected_agent` CID, `recruited_agents`, and `task_message` from session state.
2. Validates the selected agent exists in the recruited pool.
3. Constructs an `a2a.types.SendMessageRequest` and sends it via the `AgntcyFactory` client with topic-based routing (`A2AProtocol.create_agent_topic(card)`).
4. Parses the response — tries `Message` directly, then `status.message`, then falls back to raw string.
5. Yields the response as an ADK `Event` and clears `task_message`.

---

## Configuration

| Env Var | Default | Purpose |
|---|---|---|
| `RECRUITER_AGENT_URL` | `http://localhost:8881` | URL of the remote Recruiter A2A service. |
| `LITELLM_PROXY_BASE_URL` | — | LiteLLM proxy URL (optional). |
| `LITELLM_PROXY_API_KEY` | — | LiteLLM proxy API key (optional). |
| `LLM_MODEL` | *(from config)* | Model identifier passed to `LiteLlm()`. |
| `DEFAULT_MESSAGE_TRANSPORT` | *(from config)* | Transport type for `AgntcyFactory`. |
| `TRANSPORT_SERVER_ENDPOINT` | *(from config)* | Transport server endpoint. |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/agent/prompt` | Send a prompt, get a single JSON response. |
| `POST` | `/agent/prompt/stream` | Send a prompt, get streaming NDJSON. |
| `GET` | `/.well-known/agent-card.json` | A2A agent card for service discovery. |
| `GET` | `/health` | Shallow health check. |
| `GET` | `/v1/health` | Deep health check — verifies the Recruiter Service is reachable. |
| `GET` | `/transport/config` | Returns `{"transport": "A2A_HTTP"}`. |
| `GET` | `/suggested-prompts` | Returns suggested prompts from `suggested_prompts.json`. |
| `GET` | `/agents/{slug}/oasf` | Returns static OASF JSON for a given agent slug. |

### Request Body (prompt endpoints)
```json
{
  "prompt": "Find me an agent that handles shipping",
  "session_id": "optional-session-id"
}
```

If `session_id` is omitted, defaults to `"default_session"`. Sessions are in-memory (`InMemorySessionService`) and do not persist across restarts.

---

## Running

```bash
# From the recruiter supervisor directory
python main.py
# → Starts on 0.0.0.0:8882 with hot reload
```

Requires the Recruiter Service to be running on port `8881` (or wherever `RECRUITER_AGENT_URL` points).
