# Agent-to-System Bridge (agentic design pattern)

**Agent-to-System Bridge** is an agentic *design pattern*: a reusable way to let agents **invoke trusted external
systems**—ERP, emissions APIs, tariff engines—as **first-class evidence** in a decision, instead of confabulating
numbers from prose memory alone—before you pick a concrete product story (auction, hiring, logistics, etc.).

In this layout, **calling agents** plan which integration to touch, **adapters** normalize responses into stable shapes,
and **security and transport** keep scopes, identities, and retries where operators can audit them.

A **carbon accounting** voice in Coffee Agntcy can refuse to bless a route until **emissions APIs and finance systems**
return numbers the treasury will recognize—then the next reasoning step can argue with facts, not vibes.

