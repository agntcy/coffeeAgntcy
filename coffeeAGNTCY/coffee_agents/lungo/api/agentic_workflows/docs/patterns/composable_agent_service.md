# Composable Agent Service

## Agent Interaction Diagram

```mermaid
graph TD
    Catalog["Agent Catalog"]
    Carbon["Carbon Accounting Agent Service"]
    Procurement["Procurement Agent"]
    Logistics["Logistics Agent"]
    Reporting["Reporting Agent"]

    Catalog <-->|"Service Registration + Version"| Carbon
    Procurement <-->|"Emissions Request"| Carbon
    Logistics <-->|"Route Carbon Request"| Carbon
    Reporting <-->|"Reusable Carbon Facts"| Carbon
```

## Pattern

**References:**

- [Model Context Protocol](https://modelcontextprotocol.io/)
- **Inspired by:** Antonio Gullí, *Agentic Design Patterns* (Springer, 2025), Ch. 10 - Model Context Protocol (composable capabilities). [https://doi.org/10.1007/978-3-032-01402-3](https://doi.org/10.1007/978-3-032-01402-3)

**Category:** Discovery, Routing & Composition

**Composable agent service** packages an agent like a **product**: discoverable in a catalog, **versioned interfaces**,
declared expectations for reliability or latency-so procurement, operations, and reporting **reuse** the same capability
instead of forking nearly identical copies that drift apart.

Service teams ship **runtime plus contracts**; consumers declare compatible ranges; **breaking changes migrate** like
any other API the firm depends on. The pattern reduces duplication, clarifies ownership, and makes it obvious which
version answered a given request when something goes wrong.

---

## Use case

**Coffee Agntcy** is a coffee company set in a familiar supply chain: **upstream**, it depends on **farms in different
countries**, each with its own harvest rhythm, quality, and availability; **midstream**, it **buys and allocates** lots-
matching supply to commercial needs under real constraints; **downstream**, it must eventually **honor customer
promises** through operations, logistics, and finance it does not always own end to end. The company sits **between**
those worlds: much of the drama is ordinary commerce-contracts, risk, partners, and tools-rather than a single team
inside one building holding every fact.

Several parts of Coffee Agntcy need the same expertise from different angles: procurement, logistics, and
reporting each ask emissions questions in their own context. A **composable agent service** answers all of them
from one owned, versioned implementation registered in the catalog, with consumers declaring the interface ranges
they depend on. The business gains a single accountable source for a shared capability, and when an answer is
disputed, one version to trace instead of forks to reconcile.

---

## Scenario

The **carbon accounting** agent should exist **once** and be reused across every place that touches emissions-not three
nearly identical copies.

---

## Workflow

A **Workflow** section will describe how this pattern is realized once a concrete layout exists.
