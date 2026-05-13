# Supervisor–worker (agentic design pattern)

**Supervisor–worker** is an agentic *design pattern*: a reusable way to arrange *who* runs the conversation, *how* work
is split, and *how* agents talk—before you pick a concrete product story (auction, hiring, logistics, etc.).

In this layout, **one supervisor agent** owns the orchestrated workflow (such as a **LangGraph** graph). **Worker**
agents are specialists the supervisor calls when it needs a capability it does not implement itself.

---

## Goal

You want **one clear coordinator** for:

- **Sequencing** (what happens after what),
- **Branching** (which specialist to call next),
- **Policy** (business rules, guardrails, aggregation),
- **Retries and failure handling** at the orchestration layer,

…while still using **small, focused agents** (per region, per tool, per data source) that are easier to test and replace
than one monolithic “do everything” agent.

---

## Roles

|      Role      |                                                                        Responsibility                                                                        |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Supervisor** | Holds the workflow graph; interprets the user goal; plans steps; invokes workers; merges or compares their outputs; presents the next user-facing result.    |
| **Worker**     | Performs a bounded task (e.g. “return inventory”, “call payment tool”, “query directory”). Returns structured or natural-language results to the supervisor. |

Workers are **not** the primary place for cross-cutting orchestration logic—that stays with the supervisor so behavior
stays traceable.

---

## Communication and topology

Typical wiring in this pattern:

- The **supervisor** talks to **workers** over **Agent-to-Agent (A2A)** (or an equivalent RPC-style agent protocol):
  clear client/server style calls from the supervisor’s perspective.
- **Workers respond to the supervisor**; they are **not** expected to negotiate *with each other* to complete the user
  task (that would drift toward a *peer* or *group* design).

The supervisor commonly uses two interaction shapes:

1. **Unicast** — call **one** worker (e.g. “get a quote from this farm only”).
2. **Broadcast** — send the **same kind of request** to **several** workers in parallel (e.g. “inventory from all
   farms”), then **merge** answers (pick best offer, rank, aggregate, etc.).

The exact transport (message bus vs HTTP, streaming vs request/response) is an **implementation detail**; the *pattern*
is the **star topology**: hub supervisor, spoke workers.

---

## Responsibilities

**Supervisor (orchestration layer)** should own:

- Goal decomposition and **control flow** (loops, branches, “until satisfied” behavior),
- **Which** worker to call and with **what** arguments,
- **Combining** partial results and detecting contradictions or missing fields,
- **User-visible pacing** (when to ask clarifying questions).

**Workers** should own:

- **Domain or tool specialization** (one farm, one payment adapter, one directory),
- **Local** validation and formatting of their slice of the world,
- **Idempotent** or clearly scoped operations where possible, so the supervisor can retry safely.

Keeping workers **small and replaceable** is a feature: you can swap implementations or add a new worker without
redrawing the entire system.

---

## Strengths and tradeoffs

**Strengths**

- **Clear ownership** of the end-to-end story (the graph is the source of truth).
- **Parallelism** where the domain allows (broadcast to many workers).
- **Operational clarity**: logs and traces naturally anchor on “supervisor step → worker call”.

**Tradeoffs**

- The supervisor can become a **bottleneck** for design complexity—avoid turning it into a second monolith; push true
  domain logic down when it is stable.
- **Latency** scales with sequential supervisor steps unless you parallelize deliberately.
- Patterns that need **emergent multi-party dialogue** may fit **group coordination** better than strict
  supervisor–worker.

---

## Pattern fit checklist

- You need **one accountable orchestrator** for the user journey.
- Workers are **substitutable specialists**, not co-equal planners.
- Most collaboration is **supervisor ↔ worker**, not worker ↔ worker.
- You are comfortable centralizing **sequencing and policy** in one place.

If several agents must **jointly** refine a plan in the open, re-evaluate whether **group chat / coordination** is a
better fit.
