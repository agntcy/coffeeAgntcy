# Mediated Semantic Alignment

## Agent Interaction Diagram

```mermaid
graph TD
    Orchestrator["Orchestrator"]
    Aligner["Semantic Alignment Agent"]
    PartyA["Participant Agent A"]
    PartyB["Participant Agent B"]

    Orchestrator -->|"start / decide"| Aligner
    Aligner -->|"agenda + per-round messages"| Orchestrator
    Orchestrator <-->|"A2A: propose / respond"| PartyA
    Orchestrator <-->|"A2A: propose / respond"| PartyB
```

## Pattern

**References:**

- Antonio Gullí, *Agentic Design Patterns* (Springer, 2025), Ch. 7 - Multi-Agent Collaboration (Debate and Consensus).
  [https://doi.org/10.1007/978-3-032-01402-3](https://doi.org/10.1007/978-3-032-01402-3)

**Category:** Internet of Cognition

**Mediated semantic alignment** gets independent agents to agree on **what terms mean** before they act on them. A
central **Semantic Alignment Agent** runs a mediated alternating-offers loop: it turns a plain-language goal into a
shared **agenda** (a set of **issues**, each with a set of **options**), then evaluates each round's **decisions** and
detects **agreement**, but it never calls the participating agents itself.

The distinguishing move is **caller mediation**. An **orchestrator** opens the session, drives each round, and bridges
the engine to the participants over A2A. Each round the engine emits one message per participant; the orchestrator
dispatches each to the right agent, collects every reply, and posts them back together. Because the engine only ever
sees structured **offers**, each participant keeps its own reasoning **private**: an agent decides `accept`, `reject`,
or `counter_offer` on its own terms and reveals only the chosen option, never the logic behind it.

Roles alternate by round. One participant is the **proposer** and must put terms on the table via `counter_offer`; the
rest are **responders** and react to the standing offer. The loop continues until the session reaches a terminal state,
**agreed**, **broken**, or **timeout**, at which point the engine returns a validated final agreement with one chosen
option per issue plus coherence and alignment scores. The pattern transfers wherever independent parties must reconcile
vocabulary before committing: cross-vendor procurement, standards negotiation, service-level agreements, or any setting
where "we agreed" must mean the same thing to everyone who signed.

This pattern is **not** the same as:

- **Shared Intent Registry** - publishes a *canonical* goal and constraints for subscribers; mediated alignment
  *negotiates* meaning round-by-round until parties converge.
- **Shared Agent Memory** - holds operational facts (`order_id`, `PAYMENT_COMPLETE`); alignment produces an **agenda**
  and **agreement artifact**, not general task state.
- **Session Context Buffer** - ephemeral bids and counters for one deal; alignment is about **shared vocabulary** on
  issues and options, not scratchpad fields alone.
- **Decentralized Consensus Agents** - peer debate without a dedicated alignment engine and structured offer/score loop.

---

## Use case

**Coffee Agntcy** is a coffee company set in a familiar supply chain: **upstream**, it depends on **farms in different
countries**, each with its own harvest rhythm, quality, and availability; **midstream**, it **buys and allocates** lots,
matching supply to commercial needs under real constraints; **downstream**, it must eventually **honor customer
promises** through operations, logistics, and finance it does not always own end to end. The company sits **between**
those worlds: much of the drama is ordinary commerce, contracts, risk, partners, and tools, rather than a single team
inside one building holding every fact.

Commercial terms at Coffee Agntcy bind independent parties whose vocabulary carries unstated assumptions, and a
deal signed over ambiguous words is a dispute deferred. **Mediated semantic alignment** supplies a neutral
mechanism for settling meaning first: the engine structures issues and options while each participant weighs
offers against private economics and reveals only its chosen position. Consensus patterns converge on a number;
this pattern first establishes what any agreed number is actually about.

---

## Scenario

Coffee farms in **Brazil** and **Colombia** must agree on a **commodity price range** for coffee beans, expressed in
**USD per pound**. Left to plain messages the two would talk past each other: "a fair price," "the usual grade," and
"per pound" each hide different assumptions. Mediated semantic alignment forces those assumptions into an explicit
agenda first, what counts as the price range, which beans, which unit, so the farms negotiate over shared meaning
rather than over words that only look alike.

---

## Workflow

**Orchestrator** is the **caller** that owns the loop. It registers the participating agents as a multi-agentic system,
opens the session, and is the only component that ever talks to the agents. The engine stays a pure evaluator behind it.

**Semantic Alignment Agent** is the alignment engine. When the session opens it builds the **agenda**, the issues to
settle and the options available on each. On every round it scores the replies, advances the standing offer, and
reports whether the session is still **ongoing** or has reached a terminal state.

**Participant Agent A** and **Participant Agent B** are the **independent parties**. Each round the engine casts one as
**proposer** (must `counter_offer`) and the rest as **responders** (`accept`, `reject`, or `counter_offer`), and the
roles alternate. Each agent evaluates the offer against its own private economics and returns only its chosen action and
option.

**Flow in one breath**

1. The orchestrator opens the session with the goal text and a step budget; the engine returns the agenda and the first
   round's messages.
2. The orchestrator dispatches each message to its agent over A2A and collects every reply.
3. The orchestrator posts the replies back; the engine evaluates the round and returns either the next round's messages
   or a terminal status.
4. Steps 2 and 3 repeat until the session is **agreed**, **broken**, or **timeout**. On agreement the engine returns the
   final chosen option per issue with coherence and alignment scores, negotiation over shared meaning, mediated end to
   end by the caller.
