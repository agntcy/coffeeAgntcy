# Group communication / coordination (agentic design pattern)

**Group communication / coordination** is an agentic *design pattern*: a reusable way to run work when **several
specialized agents** must **see the same conversation**, **reply to one another**, and still have a **single place**
that keeps order, permissions, and progress toward the user’s goal.

In this layout, a **supervisor** (or moderator) **creates and runs a shared group channel**. **Members** join that
channel as first-class participants: they respond to the user and to **each other**, not only back to a hub in strict
turn-taking.

---

## Goal

You want **multi-party collaboration** where:

- **Context is shared** (everyone reads the same thread or transcript slice),
- **Peers can refine each other’s contributions** (clarifications, hand-offs, corrections),
- A **moderator** can still **steer** (who may speak, what phase the process is in, when to escalate or summarize),

…without forcing every interaction through a **single** orchestrator that would otherwise become the only “brain”
between specialists—as in a pure **supervisor–worker** star.

---

## Roles

|       Role        |                                                                         Responsibility                                                                          |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Supervisor**    | Sets up the group, admits or removes members, enforces phases and guardrails, may summarize or commit outcomes, and intervenes when the group stalls or drifts. |
| **Group members** | Specialized agents (e.g. farm, shipper, accountant, helpdesk) that **post into the shared conversation**, answer each other’s questions, and propose actions.   |

The supervisor is **not** the only path for member-to-member information flow: **member ↔ member** messages are a
first-class part of the design, unlike strict supervisor–worker.

---

## Communication and topology

Typical wiring in this pattern:

- A **shared conversation surface** (a “group”, “room”, or “thread”) carries **visible messages** to all members that
  belong in that phase of the workflow.
- Members use **Agent-to-Agent (A2A)** (or an equivalent protocol) to **publish and subscribe** to that shared context,
  so the system behaves like **coordination in the open**, not only private hub-and-spoke calls.
- The **supervisor** both **participates** (when helpful) and **moderates** (e.g. moving from “quote gathering” to
  “booking” to “exception handling”).

The *pattern* is a **mesh-with-moderator** topology: many-to-many communication **within** a bounded group, plus a
**clear moderator** so the user does not have to herd agents manually.

---

## Responsibilities

**Supervisor (moderation layer)** should own:

- **Lifecycle** of the group (open, invite, close; phase changes),
- **Safety and policy** (who may act, rate limits, sensitive-step confirmations),
- **Conflict resolution** when two members disagree or duplicate work,
- **User-facing synthesis** when the group produces many partial updates.

**Group members** should own:

- **Domain truth** inside their specialty (inventory, shipping constraints, invoicing rules, support policy),
- **Negotiation and clarification** *with peers* when the task genuinely requires cross-specialist alignment,
- **Action proposals** that are **scoped** (what they can commit to) and **legible** to others in the thread.

Keeping member behavior **transparent in the shared log** is what makes the pattern debuggable: the story is not hidden
inside pairwise private calls alone.

---

## Strengths and tradeoffs

**Strengths**

- **Expressiveness** for workflows that are naturally **multi-stakeholder** (logistics, incident response, procurement).
- **Less hub bottleneck** for ideation and cross-checking between specialists.
- **Human-auditable narrative**: the group transcript explains *why* a decision emerged.

**Tradeoffs**

- **Higher coordination cost**: more messages, more failure modes (talking past each other, loops, duplication).
- **Harder invariants**: you must design moderator rules so the group cannot **bypass** safety or authorization.
- **Latency and cost** can grow with “chatty” members; you may need **stricter phases** than in a tightly scripted
  graph.

When the task is “call N workers and merge lists,” **supervisor–worker** is usually simpler. When the task is “let roles
negotiate and align,” **group coordination** is often closer to the real process.

---

## Pattern fit checklist

- The outcome depends on **cross-functional alignment**, not only parallel facts from silos.
- **Specialists legitimately need to question or refine each other’s outputs** in the open.
- You can describe the process as **phases inside a shared thread** (even if implementation uses events under the hood).
- You accept investing in **moderation rules**, **membership**, and **clear completion criteria** for the group.

If every specialist only ever answers the hub and never needs peer dialogue, prefer **supervisor–worker** instead.
