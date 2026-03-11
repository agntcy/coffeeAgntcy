# Terminology

A short reference for how we name things in this repo.

Aimed at new developers and anyone exploring agentic patterns with AGNTCY components.

---

## Table of Contents

- [Terminology](#terminology)
- [Agentic design pattern (short: pattern)](#agentic-design-pattern-short-pattern)
- [Agentic use-case (short: use-case)](#agentic-use-case-short-use-case)
- [Agentic workflow (short: workflow)](#agentic-workflow-short-workflow)

---

## Agentic design pattern (short: pattern)

An agentic design pattern is a reusable architectural way of structuring how agents (or agent-like services) are
organized, orchestrated, and communicate to fulfill a capability. It answers:

- Who participates (one coordinator vs many peers, client vs server).
- How they’re coordinated (single orchestrator vs direct calls vs shared conversation).
- How they talk (transport, topology: request-reply, unicast, broadcast, group).
- So it’s the architecture of the agent system: roles, topology, and communication style, independent of the concrete
  use-case (e.g. auction vs sommelier).

A couple architectural (agentic design) patterns used throughout CoffeeAGNTCY:

1. Point-to-point (agent-to-agent): Direct A2A client–server interaction. No central coordinator. One agent (client)
   sends requests to another (server); no broadcast, no group chat or coordination. Example: Corto Sommelier/coffee
   grading.
2. Supervisor–workers: One supervisor agent holds the agentic workflow (e.g. LangGraph), receives user input, and
   delegates to worker agents via A2A. Workers do not coordinate with each other; they respond to the supervisor.
   Supports broadcast (e.g. “inventory from all farms”) and unicast (e.g. “order at Colombia”). Example: Lungo
   auction/coffee buying and Lungo recruiter/capability discovery.
3. Group chat / coordination: A supervisor sets up and moderates a shared conversation (group). Multiple specialized
   agents (e.g. farm, shipper, accountant, helpdesk) are members and talk to each other as well as to the supervisor to
   complete a task. Example: Lungo logistics/order fulfillment.

A single **(agentic design) pattern** in CoffeeAGNTCY drives one or more **use-case** implementations.

---

## Agentic use-case (short: use-case)

A concrete, goal-oriented way an agentic system is used:

- who (or what) interacts with it,
- what outcome they want, and
- the main flow of interaction.

It describes what the system does in an agent-based setting—the capability or scenario.

**In CoffeeAGNTCY we narrow that idea and tie it to architecture, an (agentic) use-case is a concrete, runnable
implementation of a distinct capability (e.g. run an auction, fulfill a logistics order, recruit/evaluate agents, act as
a sommelier).**

Each **(agentic) use-case** is built on exactly one architectural **pattern** — it’s an implementation
of that pattern to achieve a concrete goal within a defined context.

The following example (agentic) use-cases are existing in CoffeeAGNTCY:

- Point-to-point: Corto Sommelier / coffee grading.
- Supervisor-workers: Lungo auction / coffee buying, Lungo recruiter / capability discovery.
- Group chat / coordination: Lungo logistics / order fulfillment.

---

## Agentic workflow (short: workflow)

An agentic workflow is the runnable orchestrated execution flow/process of an agentic system, the steps, decisions, and
agent interactions that achieve a goal in an agentic system. It defines:

- **What runs in what order** (steps, nodes, tool calls)
- **State** that is passed and updated along the way
- **Where agents are invoked** (calls to other agents, A2A, etc.) and how their results are used

In CoffeeAGNTCY each **use-case** has an accompanied **(agentic) workflow** implementing the orchestration
logic (graph, agent loop/pipeline, state machine) that fulfills the use-case building on top of a **pattern**.

---
