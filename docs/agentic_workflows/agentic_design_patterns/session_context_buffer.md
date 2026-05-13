# Session Context Buffer (agentic design pattern)

**Session Context Buffer** is an agentic *design pattern*: a reusable way to keep a **temporary, shared scratchpad** for
one negotiation or task—bids, floors, deadlines, last counters—without polluting long-term catalogs or pretending
ephemeral chatter is permanent truth—before you pick a concrete product story (auction, hiring, logistics, etc.).

In this layout, participating agents read and write a **scoped session object** beside the conversational thread;
ownership, TTL, and field-level permissions keep the buffer honest and retirable when the deal closes or aborts.

Live **origin negotiation** in Coffee Agntcy needs exactly that: everyone sees the same “where we are now” until the
handshake or walk-away moment.

