# Composable Agent Service (agentic design pattern)

**Composable Agent Service** is an agentic *design pattern*: a reusable way to **package an agent like a
product**—discoverable in the catalog, versioned interfaces, declared SLOs—so procurement, logistics, and reporting
**reuse** the same capability instead of fork-and-drift—before you pick a concrete product story (auction, hiring,
logistics, etc.).

In this layout, service teams ship **runtime plus contracts**; consumers declare compatible ranges; breaking changes
migrate like any other API the firm depends on.

Coffee Agntcy’s **carbon accounting** agent should ride **once** across workflows that touch emissions—not three nearly
identical copies.

