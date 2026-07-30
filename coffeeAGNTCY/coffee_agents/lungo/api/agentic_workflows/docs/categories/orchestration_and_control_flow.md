# Orchestration & Control Flow

How work is structured, sequenced, delegated, recovered, and governed across one or many workflows. Patterns here place
a coordinator at the centre of the story—planning steps, handing off to specialists, chaining enrichment, looping
observe–decide–act as conditions change, or rerouting when a step fails.

**Single-workflow control** (Supervisor, Coordinator + Worker Agents, Agent Workflow Chain, Sense–Decide–Act Loop) keeps
one saga on track. **Multi-workflow orchestration** (Orchestrator Agent) resolves conflicts and global policy when
several parallel flows could step on each other. **Recovery** (Resilience & Re-Routing) defines retries, compensation,
and honest customer messaging—not just finding an alternate agent, but keeping the overall flow coherent after failure.

**Patterns:** Supervisor, Coordinator + Worker Agents, Orchestrator Agent, Agent Workflow Chain, Sense–Decide–Act Loop,
Resilience & Re-Routing

**Not to be confused with Discovery, Routing & Composition** — that category answers *who to call or compose upfront*.
Orchestration answers *how the work runs, branches, and recovers* once execution has started.
