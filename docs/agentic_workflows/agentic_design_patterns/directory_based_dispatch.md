# Directory-Based Dispatch (agentic design pattern)

**Directory-Based Dispatch** is an agentic *design pattern*: a reusable way to **choose the next specialist from intent
and context** instead of hard-wiring a single path—so the right agent answers when the situation, tags, or confidence
scores say the last callee is no longer the expert—before you pick a concrete product story (auction, hiring, logistics,
etc.).

In this layout, a **router or lightweight orchestrator** consults **directory and catalog metadata** (skills, facets,
trust labels), picks one or a few callees, and records **why** that choice was defensible—not a magical black box.

When a **shipment anomaly** lands, Coffee Agntcy might route the thread toward **weather**, **soil**, or **logistics**
depending on what the signals imply; the roster can grow without redeploying a giant switch statement.

