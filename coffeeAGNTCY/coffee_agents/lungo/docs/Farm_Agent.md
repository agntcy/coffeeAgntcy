# Adding Farm Agents (or Sub-Agents) to Lungo (Auction Supervisor Flow Only)

This document defines the **minimum configuration** and a **common contract** for adding new “farm” agents that can be supervised by the Lungo Auction Supervisor.

The current supervisor implementation uses the **A2A protocol** over **SLIM/NATS** transports (via the app-sdk transport layer).

## Minimum Configuration to Register a New Farm

In the current codebase, “registering a farm” means that the supervisor can create an A2A client that can route messages to the farm using an **AgentCard**.

## Supervisor-Side Registration and Messaging

Supervisor updates:
- `agents/supervisors/auction/graph/shared.py`:
  - Import the new farm `AGENT_CARD` and add one `farm_registry.register("<slug>", <card>)` call. `get_farm_card()` and the broadcast recipients lists in `get_all_farms_yield_inventory()` and `get_all_farms_yield_inventory_streaming()` are built from this registry.
- `agents/supervisors/auction/graph/graph.py`:
  - Check the supervisor-side routing prompt (single-farm detection and the list of known farms).

Messaging (A2A 1.x, through the app-sdk A2A client factory):
- Unicast: yield lookup and `create_order` call `prefer_transport(card, DEFAULT_MESSAGE_TRANSPORT)` on the target farm card (`common/a2a_helpers.py`), create a client, and send a `SendMessageRequest(message=...)`. `get_order_details` is the exception: it calls `prefer_transport(farm_registry.cards()[0], InterfaceTransport.SLIM)`, so that lookup stays on SLIM during a NATS run and uses the first registered farm card. The factory negotiates the connection in the order of the card's `supported_interfaces`.
- Broadcast: the supervisor calls `broadcast_message(request, recipients=[...])` on a client created from any registered farm card. A farm that fails or never answers is reported through `A2ABroadcastError`; the successful replies are kept.

> **Deprecated:** `A2AProtocol.create_agent_topic(AgentCard)` for unicast and a `FARM_BROADCAST_TOPIC` topic for broadcast. The current supervisor code uses neither (the app-sdk moved topic creation away from `A2AProtocol` in 0.5.0), so do not use them in new farms.

### 1) Transport & Routing Config

The supervisor uses these environment variables (see `config/config.py`):

```env
# Primary knobs (see config/config.py)
DEFAULT_MESSAGE_TRANSPORT=SLIM               # or NATS
SLIM_SERVER=127.0.0.1:46357                  # host:port for SLIM dataplane (no http://)
NATS_SERVER=127.0.0.1:4222                   # host:port for NATS (cards use nats://{NATS_SERVER}/...)
SLIM_SHARED_SECRET=<random-string-of-at-least-32-characters>  # same value for every SLIM peer
SLIM_ALLOW_PLACEHOLDER_SECRET=false          # true: farm servers may start SLIM with the public placeholder (local only)
# Legacy / secondary (tooling, some docs); keep aligned with the mode above
TRANSPORT_SERVER_ENDPOINT=http://127.0.0.1:46357   # or nats://127.0.0.1:4222 when using NATS
FARM_BROADCAST_TOPIC=farm_broadcast_topic_name     # deprecated: not read by the current supervisor code
```

SLIM 2.x rejects shared secrets shorter than 32 characters. The app-sdk takes the secret from the value passed in code, else from `SLIM_SHARED_SECRET`, else from a public placeholder with a warning in the log (`resolve_shared_secret()`). The supervisors (`SlimTransportConfig`) accept the placeholder. The farm servers (`CardBuilder`) refuse to start their SLIM interface when the secret is unset, empty or the placeholder, unless `SLIM_ALLOW_PLACEHOLDER_SECRET` is `true` (`common/slim_placeholder_secret.py`); Docker Compose and the Helm `local-cluster` set it for local demos. The placeholder is public: set your own random value of at least 32 characters, the same for every SLIM peer.

### 2) An AgentCard for the Farm

Each farm is represented by an `a2a.types.AgentCard` (A2A 1.x, a protobuf message; see current examples under `agents/farms/<farm>/card.py`).

Minimum fields you should provide:

- **`name`**: a stable, human-readable name (e.g., `Kenya Coffee Farm`). It is also the display name the supervisor uses in answers and the name the identity check matches.
- **`description`**: a brief description of what the farm can do.
- **`version`**: the card version.
- **`default_input_modes`** / **`default_output_modes`**: `["text"]`.
- **`capabilities`**: e.g., `AgentCapabilities(streaming=True)`.
- **`skills`**: at least an “inventory/yield” skill (`AgentSkill(id=...)` keeps its own `id`).
- **`supported_interfaces`**: an ordered list of `AgentInterface(protocol_binding=..., url=...)`. The order is the preference order: clients negotiate in this order, and the farm server treats the first entry as its required (preferred) transport. Use the `InterfaceTransport` constants from `agntcy_app_sdk.semantic.a2a.transport_types`:
  - `InterfaceTransport.SLIM_PATTERNS` with `slim://{SLIM_SERVER}/lungo/agents/<agent_id>`
  - `InterfaceTransport.NATS_PATTERNS` with `nats://{NATS_SERVER}/lungo/agents/<agent_id>`
  - `InterfaceTransport.JSONRPC` with `http://0.0.0.0:{PORT}` (the bind address of the HTTP endpoint)

Example (shortened from `agents/farms/brazil/card.py`):

```python
AGENT_CARD = AgentCard(
    name="Kenya Coffee Farm",
    description="An AI agent that returns the yield of coffee beans in pounds for the Kenya farm.",
    version="1.0.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supported_interfaces=[
        AgentInterface(protocol_binding=InterfaceTransport.SLIM_PATTERNS, url=f"slim://{SLIM_SERVER}/lungo/agents/{AGENT_ID}"),
        AgentInterface(protocol_binding=InterfaceTransport.NATS_PATTERNS, url=f"nats://{NATS_SERVER}/lungo/agents/{AGENT_ID}"),
        AgentInterface(protocol_binding=InterfaceTransport.JSONRPC, url=f"http://0.0.0.0:{PORT}"),
    ],
)
```

Card fields from A2A v0.3 that no longer exist (**deprecated, do not set them**):

| Old field (A2A v0.3) | Replacement (A2A 1.x) |
|---|---|
| `id` (stable card ID) | none; use `name`. Only `AgentSkill(id=...)` still has an `id` |
| `url` | the `url` of the first `supported_interfaces` entry |
| `preferred_transport` | the first entry of `supported_interfaces` |
| `additional_interfaces` / `AgentInterface(transport=...)` | the rest of `supported_interfaces` / `AgentInterface(protocol_binding=...)` |
| `defaultInputModes` / `defaultOutputModes` | `default_input_modes` / `default_output_modes` |
| `supportsAuthenticatedExtendedCard` | removed from the card |
| lowercase transport strings (`"slim"`, `"nats"`, `"jsonrpc"`) | `InterfaceTransport` constants (`SLIM_PATTERNS`, `NATS_PATTERNS`, `JSONRPC`) |

The OASF records under `agents/**/oasf/` are still written in the A2A v0.3 card shape (`url`, `preferredTransport`, `additionalInterfaces`) on purpose: the recruiter and the frontend read that shape.

The supervisor currently expects new farms to be wired into:

- A new card module: `agents/farms/<new_farm>/card.py` exporting `AGENT_CARD`.
- The farm registry in `agents/supervisors/auction/graph/shared.py` (one `farm_registry.register(...)` call; `get_farm_card()` and the broadcast recipients are derived from it).
- The supervisor router in `agents/supervisors/auction/graph/graph.py` (the `_supervisor_node` prompt currently hard-codes the known farms: Brazil, Colombia, Vietnam).

### 3) Farm A2A Server (Interfaces + Reply Contract)

Your farm runs an A2A server (see existing `agents/farms/<farm>/farm_server.py`) that:

- Builds a `DefaultRequestHandler(agent_executor=..., task_store=InMemoryTaskStore(), agent_card=AGENT_CARD)`. The `agent_card` argument is required in a2a-sdk 1.x.
- Serves every entry of the card's `supported_interfaces`, each in its own app-sdk session (`session.add_a2a_card(card, handler)`), so one unavailable transport (for example NATS) cannot stop the others. A startup failure on the first, preferred interface is fatal; failures on the others are logged and skipped.
- Also answers A2A v0.3 JSON-RPC calls on its HTTP endpoint (`A2AServerConfig(..., enable_v0_3_compat=True)` through `builder.override("jsonrpc", ...)`, with a `clone_card(AGENT_CARD)` so the module card is not edited), because the recruiter interviewer still speaks v0.3. The logistics servers (`agents/logistics/*/server.py`) do not do this: their cards advertise SLIM only, their HTTP port serves `/v1/health` and the card, and nothing calls their JSON-RPC over HTTP, so their HTTP JSON-RPC is A2A v1.0 only (the pre-migration app also answered v0.3 there).
- Replies with exactly one final `Message` (see below). Do not return a `Task`: in a2a-sdk 1.x an executor that enqueues a `Message` must not enqueue anything else afterwards.

In practice, the supervisor sends:

- **Unicast** requests to one farm's card when querying a single farm.
- **Broadcast** requests with a `recipients` list (one identifier per registered farm) when querying all farms.

The supervisor currently expects responses to be in **plain text**, in the first text part of the reply message.

The reply is built like this (see `agents/farms/<farm>/agent_executor.py`):

```python
from a2a.types import Message, Part, Role

message = Message(
    message_id=str(uuid4()),
    role=Role.ROLE_AGENT,
    metadata={"name": AGENT_CARD.name},   # the supervisor reads the farm name from here
    parts=[Part(text=output)],
)
await event_queue.enqueue_event(message)
```

Errors are raised, not returned as text: use `ContentTypeNotSupportedError`, `InternalError` and `UnsupportedOperationError` from `a2a.utils.errors`.

> **Deprecated (A2A v0.3 shapes, do not use):** `new_agent_text_message(...)` / `new_task(...)` with `TaskStatusUpdateEvent` and `TextPart` replies, enum values such as `Role.agent` and `TaskState.completed` (now `Role.ROLE_AGENT`, `TaskState.TASK_STATE_COMPLETED`), reading the reply as `result.parts[0].text` (now `get_message_text(message)` from `a2a.helpers`, or `response_text(response)` from `common/a2a_helpers.py`), and a plain-dict `metadata` on the received message (it is a protobuf `Struct` now; use `message_metadata(message)` from `common/a2a_helpers.py`).

If you have identity verification enabled, the supervisor verifies identity by matching the farm's identity app name against `AgentCard.name` (see `verify_farm_identity()` in `agents/supervisors/auction/graph/tools.py`).


## The Common Farm Agent Contract

Regardless of the internal framework, each farm should implement the same **external contract**.

### Inputs

The supervisor sends natural-language messages. In practice, they fall into these categories:

#### A) Inventory / Yield / Availability Queries

Examples:

- `"How much coffee does the Kenya farm have?"`
- `"What is your current yield?"`
- Broadcast variant: `"What yield do the farms have?"`

#### B) Order Creation

The supervisor’s tool sends a message of the form:

- `"Create an order with price <price> and quantity <quantity>"`

The farm should interpret this as an order request and return a confirmation message.

### Outputs (Expected by the Supervisor)

The supervisor expects the A2A response to contain a **first text part**.

#### A) Inventory Response Format

Return only the yield/inventory value with a unit.

Example:

```text
5000 lbs
```

#### B) Order Response Format

Return plain text that includes an `order_id:` line.

Example:
```text
order_id: 54321
```

## Reusable Prompt Template for Farm Agents

Use this as the **system prompt** for any farm agent, regardless of internal implementation.

> **Note:** Might need to tweak the prompt slightly for different frameworks/models.

```text
You are a coffee farm manager in {FARM_COUNTRY} who delegates farm cultivation and global sales.

Based on the user's message, determine whether it is related to 'inventory' or 'orders'.
- Respond with 'inventory' if the message is about checking yield, stock, product availability, or specific coffee item details.
- Respond with 'orders' if the message is about checking order status, placing an order, or modifying an existing order.
- If unsure, respond with 'general'.

Inventory behavior:
- Return a random yield estimate for the coffee farm in {FARM_COUNTRY}.
- Make sure the estimate is a reasonable value and in pounds.
- Respond with only the yield estimate.
- If the user asked in lbs or pounds, respond in pounds.
- If the user asked in kg or kilograms, convert to kg and respond with that value.

Orders behavior:
- You are an order assistant. Based on the user's question and the following order data, provide a concise and helpful response.
- If they ask about a specific order number, provide its status.
- If they ask about placing an order, generate a random order ID and tracking number.

Output rules:
- Output must be plain text.
- For inventory, return a single line like: "5000 lbs".
- For order creation, include an order ID line like: "order_id: 54321".

```

## Adding Farm Agents by Framework

You can implement a farm with different frameworks, as long as it produces the same **plain-text** outputs for inventory and order creation.

When adding a new farm, you can copy an existing farm directory as a starting point and adjust:
- `agent.py`
- `agent_executor.py`
- `card.py`
- `farm_server.py`

### Adding Tracing Support

Add tracing support to the farm server using `ioa-observe-sdk`. To do this, follow the pattern used by existing farms:

```python
from ioa_observe_sdk.decorators import agent, graph, tool

@graph(name="farm_graph")
def build_graph():
    ...

@agent(name="farm_agent")
def run_agent(...):
    ...

@tool(name="some_tool")
def some_tool_fn(...):
    ...
```

### LangGraph Farm

Where to look:
- `agents/farms/<farm>/agent.py`

Pattern:
- Route to two paths:
  - `inventory` (yield/availability)
  - `orders` (create order)
- Reuse a consistent prompt for inventory and another for order creation following the reusable prompt template above.
- Add tracing support to the farm server using `ioa-observe-sdk`.

### LlamaIndex farm

Where to look:
- `agents/farms/<farm>/agent.py`

Pattern:
- Use LlamaIndex internally (tools / retrieval / workflows) to implement:
  - inventory/yield responses
  - order creation responses
- Use the reusable prompt template above.
- Add a simple router (inventory vs orders) and return a single **plain-text** response.
- Add tracing support to the farm server using `ioa-observe-sdk`.

### Adding a new framework

You can use any agent framework as long as the farm keeps the same outward contract:
- Implement the farm logic in `agents/farms/<farm>/agent.py`.
- Support two request types:
  - Inventory/yield (messages like `"How much coffee does the Kenya farm have?"` or `"What yield do the farms have?"`)
  - Order creation (messages like `"Create an order with price <price> and quantity <quantity>"`)
- Use the reusable prompt template above.
- Always return a single plain-text response (the supervisor reads the first text part).
- Keep the farm discoverable by the supervisor via the farm `AgentCard` wiring.
- Add tracing support to the farm server using `ioa-observe-sdk`.
