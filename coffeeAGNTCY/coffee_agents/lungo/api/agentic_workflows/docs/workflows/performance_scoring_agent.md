# Performance Scoring Agent

## Agent Interaction Diagram

```mermaid
graph TD
    Procurement["Procurement Agent"]
    Telemetry["Telemetry Collector"]
    Outcomes["Business Outcomes Store"]
    Scoring["Performance Scoring Agent"]
    Feedback["Feedback / Reflection Agent"]

    Procurement -->|"Run Metadata"| Telemetry
    Outcomes -->|"Cost Time Carbon Quality"| Scoring
    Telemetry -->|"Trace + Timing Data"| Scoring
    Scoring -->|"KPI Score"| Feedback
```

## Pattern

**References:**

- **Inspired by:** Antonio Gullí, *Agentic Design Patterns* (Springer, 2025), Ch. 11 - Goal Setting and Monitoring and Ch. 19 - Evaluation and Monitoring. [https://doi.org/10.1007/978-3-032-01402-3](https://doi.org/10.1007/978-3-032-01402-3)

**Category:** Observability & Performance Accountability

A **performance scoring agent** measures how well agentic runs meet **declared KPIs**-cost, time, carbon, quality, or
whatever leadership actually names-so improvement budgets go to what **measurably** works, not to whoever tells the
prettiest story. Scores are tied to **transparent formulas** and comparable inputs.

The scoring agent joins **telemetry** to **business outcomes**, publishes results, and can feed **reflection** and
**feedback** loops elsewhere. The pattern institutionalizes accountability for automation the same way finance
institutionalizes variance analysis.

---

## Use case

**Coffee Agntcy** is a coffee company set in a familiar supply chain: **upstream**, it depends on **farms in different
countries**, each with its own harvest rhythm, quality, and availability; **midstream**, it **buys and allocates** lots-
matching supply to commercial needs under real constraints; **downstream**, it must eventually **honor customer
promises** through operations, logistics, and finance it does not always own end to end. The company sits **between**
those worlds: much of the drama is ordinary commerce-contracts, risk, partners, and tools-rather than a single team
inside one building holding every fact.

Automated sourcing at Coffee Agntcy has to justify itself in the units leadership already budgets: cost, time,
carbon, and quality. The **performance scoring agent** joins run telemetry with recorded business outcomes and
publishes KPI scores under transparent formulas, giving the company a comparable record of how its agentic runs
perform across cycles. Telemetry explains how a run unfolded and business outcomes show what it achieved; scoring
turns those inputs into comparable numbers the firm can defend.

---

## Scenario

**Procurement cycles** should be judged on the **triple** leadership claims to care about.

---

## Workflow

A **Workflow** section will describe how this pattern is realized once a concrete layout exists.
