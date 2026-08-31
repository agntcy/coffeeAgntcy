# Internet of Cognition — pattern intake & gap matrix

Living reference for proposing and authoring IoC patterns in Lungo. Updated when the catalog grows.

---

## Category scope (Internet of Cognition)

**In scope:** queryable cognitive substrate — working task state, governed reference data, session scratchpads,
ordered decision history, shared intent, alignment artifacts, and team context that agents read/write beyond
point-to-point messages.

**Out of scope:**

| Adjacent category | Holds |
|-------------------|--------|
| Observability & Performance Accountability | How the system ran (spans, KPI scores) |
| Orchestration & Control Flow | Who coordinates whom, control flow |
| Multi-Agent Communication & Collaboration | Transport and messaging patterns |
| Discovery, Routing & Composition | Finding and selecting agents |
| Governance, Policy & Human Oversight | Approval gates, policy enforcement |

---

## Existing IoC patterns (baseline)

| Pattern | Shared artifact | Lifetime | Primary operation |
|---------|-----------------|----------|-------------------|
| Shared Agent Memory | Operational facts for a task/MAS | Task / MAS scoped | retain / recall |
| Shared Knowledge Store | Curated reference records | Long-lived | query / ingest |
| Session Context Buffer | Live negotiation scratchpad | Session / TTL | read / write scoped fields |
| Event Ledger (Episodic Memory) | Ordered decision/tool trace | Append-only history | append / replay |

---

## Outshift IoC / L9 mapping

| L9 / Outshift concept | Lungo coverage (before this intake) | Gap |
|-----------------------|-------------------------------------|-----|
| **SIEP** — semantic information exchange | Partial (Shared Agent Memory, Knowledge Store) | Structured semantic payloads beyond facts |
| **CIP** — cognition interoperability | Partial (Session hierarchy in L9 specs) | Session/episodic cognition model in catalog |
| **SAB** — semantic alignment broadcast | **Missing** | Shared intent / constraint broadcast |
| **TFP** — team formation via polling | **Missing** | Dynamic coalition assembly |
| **SAO / alignment engines** | Draft doc only (`mediated_semantic_alignment.md`) | Not catalogued; no category marker |
| **CFN retain/recall** | Described in Shared Agent Memory | Other patterns lack CFN hook notes |

---

## New patterns added (this intake)

| Pattern | Source inspiration | Boundary vs existing four |
|---------|------------------|---------------------------|
| **Mediated Semantic Alignment** | SAO, L9 alignment; in-repo draft | Agreement on *terms* before action; not memory, ledger, or scratchpad |
| **Team Formation via Polling** | TFP (L9) | *Who joins the task*; not facts, knowledge, or session bids |
| **Shared Intent Registry** | SAB (L9), intent-scoped cognition | *Canonical goal + constraints* all agents query; not operational facts (memory) or ephemeral session state |

---

## Intake checklist (use for every candidate)

- [ ] **Category fit** — queryable cognitive state for agent decisions?
- [ ] **Multi-agent** — requires shared substrate or 2+ parties?
- [ ] **Distinct** — "not the same as" section names all overlapping IoC patterns?
- [ ] **Documentable** — mermaid diagram + Coffee Agntcy use case + scenario + workflow?
- [ ] **References** — Gullí chapter, multi-agent.wiki, Outshift/L9, or Fowler where applicable?
- [ ] **Catalog** — entry in `starting_workflows.json` with `pattern_category: Internet of Cognition`?
- [ ] **Category doc** — listed in `docs/categories/internet_of_cognition.md`?

---

## Authoring locations

| Artifact | Path |
|----------|------|
| Pattern reference | `docs/workflows/{slug}.md` |
| Catalog entry | `starting_workflows.json` |
| Category charter | `docs/categories/internet_of_cognition.md` |
| Terminology | repo root `docs/TERMINOLOGY.md` |

---

## Backlog (not implemented — evaluate later)

| Candidate | Why deferred |
|-----------|--------------|
| Procedural Playbook Store | Overlaps Shared Knowledge Store unless scoped to *how* not *what* |
| Belief / World-Model Reconciliation | Strong pattern; needs clearer CFN data model |
| Intent-Scoped Authorization (CASA) | Borders Governance category |
| L9 Session/Episode Carrier | Protocol-shaped; may belong in integration docs first |

---

## External sources (mining order)

1. In-repo `docs/workflows/*.md` and `docs/categories/*.md`
2. [outshift-open/ioc-protocols-models](https://github.com/outshift-open/ioc-protocols-models) — SIEP, CIP, SAB, TFP
3. Gullí, *Agentic Design Patterns* (2025) — especially Ch. 8, 14, 7
4. [multi-agent.wiki](https://multi-agent.wiki) — blackboard, coordination
5. `lungo/ioc/README.md` — CFN implementation hooks
