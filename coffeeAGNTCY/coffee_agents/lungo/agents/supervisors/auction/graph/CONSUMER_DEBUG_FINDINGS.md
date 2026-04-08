# `logging_consumer` Not Firing — Root Cause Analysis

## Symptom

The `LoggingInterceptor` prints `=== A2A REQUEST [message/send] ===` as expected, but the `logging_consumer` never prints `=== A2A Event ===`.

## How Interceptors vs Consumers Work

| Concept | When it fires | Mechanism |
|---|---|---|
| **Interceptor** | Before the request is sent (outbound) | Called by transport layer via `_apply_interceptors()` |
| **Consumer** | After a response is received (inbound) | Called by `BaseClient.consume()` inside `send_message()` / `_process_response()` |

The key difference: interceptors fire during request dispatch, consumers fire during response processing — and **only** from `BaseClient.send_message()`.

## Root Cause

### 1. Broadcast methods bypass `consume()`

`A2AExperimentalClient.broadcast_message()` and `broadcast_message_streaming()` go directly to the transport and **never call `self.consume()`**. The interceptor still fires because those methods explicitly call `_apply_interceptors()`, but no consumer callback is ever invoked.

**Source**: [`experimental_patterns.py`](../../.venv/lib/python3.13/site-packages/agntcy_app_sdk/semantic/a2a/client/experimental_patterns.py) — `broadcast_message()` applies interceptors but does not call `self.consume()` on responses.

### 2. Consumers are not passed to all client creation calls

| Function | Interceptor passed? | Consumer passed? |
|---|---|---|
| `get_farm_yield_inventory` | ✅ `LoggingInterceptor()` | ✅ `logging_consumer` |
| `get_all_farms_yield_inventory` | ❌ | ❌ |
| `get_all_farms_yield_inventory_streaming` | ✅ `LoggingInterceptor()` | ❌ |
| `create_order` | ❌ | ❌ |
| `get_order_details` | ❌ | ❌ |

Only `get_farm_yield_inventory` passes the consumer. Even there, consumers will only fire if the response is successfully received (see point 3).

### 3. Retries may prevent consumer invocation

`send_a2a_with_retry` iterates `client.send_message(message)`. Inside `BaseClient.send_message()`, `consume()` is called **after** the transport returns a response:

```python
# BaseClient.send_message (non-streaming path):
response = await self._transport.send_message(params, ...)
result = (response, None) if isinstance(response, Task) else response
await self.consume(result, self._card)   # <-- only reached on success
yield result
```

If the transport raises an exception (e.g., SLIM timeout), the consumer never fires for that attempt. If all retry attempts fail, the consumer is never called at all.

## Call Flow Diagram

```
get_farm_yield_inventory()
  └─ send_a2a_with_retry(client, message)
       └─ async for event in client.send_message(message):
            # client is A2AExperimentalClient
            └─ delegates to self._client.send_message()  (BaseClient)
                 └─ transport.send_message(params)
                      └─ _apply_interceptors("message/send", ...)  ← INTERCEPTOR FIRES ✅
                 └─ await self.consume(result, self._card)          ← CONSUMER FIRES ✅ (if no exception)

get_all_farms_yield_inventory_streaming()
  └─ client.broadcast_message_streaming(request, recipients)
       # A2AExperimentalClient method
       └─ _apply_interceptors("message/send", payload)             ← INTERCEPTOR FIRES ✅
       └─ transport.broadcast(...)
       └─ yields responses directly                                ← consume() NEVER CALLED ❌
```

## Recommendations

### Option A: Add logging directly in broadcast response processing

Since `broadcast_message` / `broadcast_message_streaming` don't invoke consumers, add explicit logging where you process broadcast responses:

```python
# In get_all_farms_yield_inventory_streaming, after receiving each response:
async for response in response_stream:
    print(f"=== A2A Broadcast Response ===")
    print(f"Response: {response}")
    # ... existing processing ...
```

### Option B: Ensure consumer is passed for single-farm calls

For `create_order` and `get_order_details`, pass the consumer if you want response logging:

```python
client = await a2a_client_factory.create(
    card,
    interceptors=[LoggingInterceptor()],
    consumers=[logging_consumer],
)
```

### Option C: Make the consumer body more informative

The current consumer body only prints a static string. Enrich it so it's obvious when it does fire:

```python
async def logging_consumer(event: ClientEvent | Message, agent_card: AgentCard) -> None:
    print(f"=== A2A Event from {agent_card.name if agent_card else 'unknown'} ===")
    if isinstance(event, Message):
        for part in event.parts:
            if hasattr(part.root, "text"):
                print(f"  Text: {part.root.text[:200]}")
    elif isinstance(event, tuple):
        task, update = event
        print(f"  Task ID: {task.id}")
        print(f"  Status: {task.status.state if task.status else 'N/A'}")
        if update:
            print(f"  Update type: {type(update).__name__}")
```

## Summary

The consumer is correctly defined and correctly passed in `get_farm_yield_inventory`. The reason it's not logging is most likely that the **active code path is a broadcast method** (`get_all_farms_yield_inventory_streaming`), which never invokes `consume()`. This is a limitation of the `A2AExperimentalClient` — broadcast operations don't go through the standard `BaseClient.send_message()` flow where consumers are called.
