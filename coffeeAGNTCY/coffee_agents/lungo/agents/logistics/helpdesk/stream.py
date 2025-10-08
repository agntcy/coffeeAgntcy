# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import Request
from sse_starlette.sse import EventSourceResponse

from agents.logistics.helpdesk.store.event import OrderEvent
from agents.logistics.helpdesk.store.singleton import global_store

logger = logging.getLogger("lungo.helpdesk.stream")


def _serialize(ev: OrderEvent) -> dict:
  """
  Convert an OrderEvent to a JSON-serializable dict.
  Removed: connection_id, final (client derives completion from state).
  """
  return {
    "order_id": ev.order_id,
    "sender": ev.sender,
    "receiver": ev.receiver,
    "message": ev.message,
    "state": ev.state,
    "timestamp": ev.timestamp.isoformat(),
  }


async def sse_generator(request: Request, _ignored: str) -> AsyncGenerator[dict, None]:
  """
  SSE stream:
    - Starts with latest order (or waits for first).
    - Emits event data for appended events.
    - Emits 'switch' meta-event when a newer order appears.
    - Emits heartbeat if nothing changes within timeout windows.
  """
  # Discover or wait for first order
  latest = await global_store.latest_order()
  if latest:
    last_seq, current_order_id = latest
  else:
    last_seq = 0
    while True:
      if await request.is_disconnected():
        return
      new_orders, new_max = await global_store.wait_for_new_orders(last_seq, timeout=30.0)
      if new_orders:
        last_seq = new_max
        current_order_id = new_orders[-1][1]
        break
      yield {"event": "heartbeat", "data": "{}"}

  # Emit current snapshot of selected order
  events = await global_store.get(current_order_id)
  index = len(events)
  for ev in events:
    yield {"data": json.dumps(_serialize(ev))}

  # Main loop: race between new events for current order vs new order creation
  while True:
    if await request.is_disconnected():
      break

    events_task = asyncio.create_task(
      global_store.wait_for_events(current_order_id, index, timeout=30.0)
    )
    new_order_task = asyncio.create_task(
      global_store.wait_for_new_orders(last_seq, timeout=30.0)
    )
    done, pending = await asyncio.wait(
      {events_task, new_order_task},
      return_when=asyncio.FIRST_COMPLETED,
    )
    for t in pending:
      t.cancel()

    emitted = False

    # Check if a newer order appeared (switch context)
    if new_order_task in done:
      new_orders, max_seq = await new_order_task
      if new_orders:
        last_seq = max_seq
        current_order_id = new_orders[-1][1]
        snapshot = await global_store.get(current_order_id)
        index = len(snapshot)
        yield {
          "event": "switch",
          "data": json.dumps({
            "order_id": current_order_id,
            "seq": last_seq,
          }),
        }
        for ev in snapshot:
          yield {"data": json.dumps(_serialize(ev))}
        emitted = True

    # Emit new events for current order
    if events_task in done and not emitted:
      new_events, new_index = await events_task
      if new_events:
        index = new_index
        for ev in new_events:
          yield {"data": json.dumps(_serialize(ev))}
        emitted = True

    # Heartbeat if nothing happened (timeout)
    if not emitted:
      yield {"event": "heartbeat", "data": "{}"}


async def stream_handler(request: Request) -> EventSourceResponse:
  """
  HTTP handler wiring the SSE generator.
  Query param 'order_id' ignored (kept for compatibility).
  """
  return EventSourceResponse(sse_generator(request, request.query_params.get("order_id", "")))