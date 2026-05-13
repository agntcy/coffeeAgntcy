# Recruiter (agentic design pattern)

**Recruiter** is an agentic *design pattern* name used in the CoffeeAGNTCY/Lungo **workflow catalog** for flows whose
main job is **on-demand discovery**: finding, comparing, or short-listing **remote agents and capabilities** (for
example from a **directory** or registry), then handing a **small, trustworthy answer** back to the user or to a
downstream workflow.

Structurally, a recruiter-style flow is usually implemented as **supervisor–worker** orchestration (one coordinator, a
few clear callees). The **“Recruiter”** label highlights the **discovery semantics**—*who exists, what do they offer,
are they eligible*—rather than day-to-day task execution like auction bidding or order fulfillment.

---

## Goal

You want a **controlled discovery loop** when:

- Capabilities live in a **catalog** that can change over time (agents register, retire, or update cards),
- The user question is underspecified (“find me something that can …”) and needs **search + ranking + explanation**,
- You must keep **policy in one place** (allow-lists, scoring, consent, rate limits) while still calling out to **many
  possible providers**,

…without hard-coding a fixed set of agent endpoints for every new prompt.

---

## Roles

|               Role                |                                                                              Responsibility                                                                              |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Recruiter**                     | Owns the discovery workflow: parses intent, queries the directory, may probe candidates, ranks results, explains trade-offs.                                             |
| **Directory / registry**          | System-of-record for **what can be discovered** (agent cards, skills, endpoints, trust metadata). Answers structured lookups; does not replace the recruiter’s judgment. |
| **Candidate agents** *(optional)* | Remote specialists surfaced by the directory. The recruiter may **invoke** them read-only (health checks, capability probes) or defer execution to another workflow.     |

---

## Communication and topology

Typical wiring in this pattern:

- **Recruiter → directory** queries are **read-mostly** and should be **cheap and cacheable** where possible (lists,
  filters, facets).
- **Recruiter → candidate** calls (when used) are **purpose-bound** (“verify this card”, “fetch tool schema”), not an
  open-ended group conversation—unless you *explicitly* graduate the scenario to **group coordination**.
- Results flow **back through the recruiter** so the user sees **one coherent narrative** (what matched, why, what to do
  next).

The *pattern* is still a **star** (or a shallow star with a dedicated registry spoke), but the **center of gravity** is
**selection**, not long-running multi-party negotiation.

---

## Responsibilities

**Recruiter (orchestration layer)** should own:

- **Query shaping** (turning vague asks into directory queries and follow-ups),
- **Ranking and filtering** (hard constraints vs soft preferences),
- **Safety** (do not leak private registry fields; do not call unknown endpoints without checks),
- **Traceability** (which directory version, which candidates were considered).

**Directory / registry** should own:

- **Canonical metadata** for discoverable agents (identity, interfaces, ownership, lifecycle),
- **Stable keys** so the recruiter can refer to results without ambiguous free text alone.

**Candidate agents** (when involved) should own:

- **Truth about their own capability** (what they implement today),
- **Bounded responses** to recruiter probes so discovery cannot turn into unbounded chatter.

---

## Strengths and tradeoffs

**Strengths**

- **Scales with ecosystem growth**: new agents can appear without rewriting the recruiter graph.
- **User-legible outcomes**: “here are three options and why” fits product flows better than raw registry dumps.
- **Operational separation** between **catalog governance** and **selection logic**.

**Tradeoffs**

- **Stale or noisy directories** propagate directly into bad recommendations—treat catalog quality as part of the
  system’s SLO.
- **Over-calling candidates** for “freshness” can explode latency and cost; prefer phased discovery.
- If discovery turns into **ongoing negotiation between equals**, you are drifting toward **group coordination**; that
  may deserve a different workflow shape.

---

## Pattern fit checklist

- You have (or plan) a **registry** that lists agents or capabilities.
- Users routinely ask **which** agent or **which** tool chain should run next.
- You want **one accountable selector** that can explain its picks.
- Execution of the discovered work can happen **later** (another workflow) or **inline**, but discovery stays a distinct
  concern.

If there is **no shared catalog** and only a single fixed callee, **point-to-point** or a minimal **supervisor–worker**
graph without discovery may be simpler.
