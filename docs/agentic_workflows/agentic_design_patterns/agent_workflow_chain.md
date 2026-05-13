# Agent Workflow Chain (agentic design pattern)

**Agent Workflow Chain** is an agentic *design pattern*: a reusable way to **break a complex goal into ordered agent
steps**, each enriching **shared state** so later specialists inherit constraints instead of re-discovering what earlier
steps already proved—before you pick a concrete product story (auction, hiring, logistics, etc.).

In this layout, **specialists run in sequence** (or in a shallow DAG): each step reads the same evolving record—quality
floors, commercial bands, diligence flags—and writes its slice back under schema before the next agent runs.

Coffee Agntcy’s procurement desk is the familiar picture: **farm data**, then **quality**, then **pricing**, then
**commitment**—each hop adds something the firm can show a buyer, a grower, or finance without embarrassment.

