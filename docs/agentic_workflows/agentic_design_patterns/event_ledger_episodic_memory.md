# Event Ledger (Episodic Memory) (agentic design pattern)

**Event Ledger (Episodic Memory)** is an agentic *design pattern*: a reusable way to **append a faithful history of
agent decisions**—prompts, tool calls, policy checks—so teams can **replay** timelines after failure and explain *which
step* introduced a bad assumption—before you pick a concrete product story (auction, hiring, logistics, etc.).

In this layout, instrumented agents and tools emit **structured spans** into an observability backbone; correlation ties
those spans to business objects like lots, orders, or shipments.

When a **shipment fails** in Coffee Agntcy, operations does not want poetry—they want the same story the machines
already told, end to end.

