# Coordinator + Worker Agents (agentic design pattern)

**Coordinator + Worker Agents** is an agentic *design pattern*: a reusable way to **separate planning from
execution**—one agent keeps the work breakdown and completion story while **specialists** perform bounded slices
(warehouse, customs, carriers) without each owning the whole saga—before you pick a concrete product story (auction,
hiring, logistics, etc.).

In this layout, a **coordinator** assigns tasks, tracks status, and reconciles outcomes; **workers** return structured
results so retries, escalations, and “done” semantics stay legible under workflow and identity.

Coffee Agntcy’s **order fulfillment** chapter fits naturally: someone must **orchestrate** releases, filings, and
bookings while still letting each function speak its own operational language.

