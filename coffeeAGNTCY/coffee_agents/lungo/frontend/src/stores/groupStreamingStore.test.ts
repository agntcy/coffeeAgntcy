/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { beforeEach, describe, expect, it, vi } from "vitest"
import {
  handleGroupStreamPayload,
  useGroupStreamingStore,
} from "./groupStreamingStore"
import { NDJSON_STREAMING_STATUS } from "./ndjsonStreamingStatus"
import type { SupplyChainStreamEvent } from "./supplyChainEvents"

const logisticsStep = {
  order_id: "order-1",
  sender: "Supervisor",
  receiver: "Tatooine Farm",
  message: "Need 500 lbs",
  timestamp: "2026-01-01T00:00:00Z",
  state: "RECEIVED_ORDER",
}

function makeActions() {
  return {
    addEvent: vi.fn(),
    addNegotiationEvent: vi.fn(),
    setFinalResponse: vi.fn(),
    setSessionId: vi.fn(),
  }
}

describe("handleGroupStreamPayload", () => {
  it("keeps the logistics Python-dict string path", () => {
    const actions = makeActions()
    const response = `{'order_id': 'order-1', 'sender': 'Supervisor', 'receiver': 'Tatooine Farm', 'message': 'Need 500 lbs', 'timestamp': '2026-01-01T00:00:00Z', 'state': 'RECEIVED_ORDER'}`

    const result = handleGroupStreamPayload(
      { response, session_id: "s-1" },
      actions,
    )

    expect(result).toBeUndefined()
    expect(actions.setSessionId).toHaveBeenCalledWith("s-1")
    expect(actions.addEvent).toHaveBeenCalledWith(logisticsStep)
    expect(actions.addNegotiationEvent).not.toHaveBeenCalled()
  })

  it("parses a JSON string first, so apostrophes survive", () => {
    const actions = makeActions()
    const response = JSON.stringify({
      ...logisticsStep,
      message: "We can't ship before Friday",
    })

    handleGroupStreamPayload({ response }, actions)

    expect(actions.addEvent).toHaveBeenCalledWith(
      expect.objectContaining({ message: "We can't ship before Friday" }),
    )
  })

  it("ends the stream on a plain final response", () => {
    const actions = makeActions()

    const result = handleGroupStreamPayload({ response: "All done" }, actions)

    expect(result).toBe("stop")
    expect(actions.setFinalResponse).toHaveBeenCalledWith("All done")
  })

  it.each([
    {
      caseName: "status",
      response: { type: "status", state: "selected", message: "ambiguous" },
    },
    {
      caseName: "message",
      response: {
        type: "message",
        seq: 3,
        from: "supplier_b",
        to: ["buyer"],
        kind: "negotiation",
        phase: "round_1",
        plan_version: 0,
        reply_to: 2,
        body: "We can't do Nov 18, it's too tight.",
      },
    },
  ])("routes a JSON object $caseName event to the negotiation list", (c) => {
    const actions = makeActions()

    const result = handleGroupStreamPayload(
      { response: c.response, session_id: "s-2" },
      actions,
    )

    expect(result).toBeUndefined()
    expect(actions.addNegotiationEvent).toHaveBeenCalledTimes(1)
    expect(actions.addNegotiationEvent.mock.calls[0][0].type).toBe(
      c.response.type,
    )
    expect(actions.addEvent).not.toHaveBeenCalled()
  })

  it("ignores an object that is not a known event", () => {
    const actions = makeActions()

    handleGroupStreamPayload({ response: { type: "mystery" } }, actions)

    expect(actions.addNegotiationEvent).not.toHaveBeenCalled()
    expect(actions.addEvent).not.toHaveBeenCalled()
  })
})

describe("useGroupStreamingStore negotiation events", () => {
  beforeEach(() => {
    useGroupStreamingStore.getState().reset()
  })

  const status = (state: string, message?: string): SupplyChainStreamEvent => ({
    type: "status",
    state,
    message,
  })

  it("collects events in order and promotes CONNECTING to STREAMING", () => {
    useGroupStreamingStore.setState({
      status: NDJSON_STREAMING_STATUS.CONNECTING,
    })
    const { addNegotiationEvent } = useGroupStreamingStore.getState()

    addNegotiationEvent(status("selected"))
    addNegotiationEvent(status("started"))

    const state = useGroupStreamingStore.getState()
    expect(state.negotiationEvents.map((e) => e.type)).toEqual([
      "status",
      "status",
    ])
    expect(state.status).toBe(NDJSON_STREAMING_STATUS.STREAMING)
  })

  it("turns an error status event into the store error", () => {
    useGroupStreamingStore
      .getState()
      .addNegotiationEvent(status("error", "An internal error occurred."))

    const state = useGroupStreamingStore.getState()
    expect(state.status).toBe(NDJSON_STREAMING_STATUS.ERROR)
    expect(state.error).toBe("An internal error occurred.")
  })

  it("clears negotiation events on reset", () => {
    const store = useGroupStreamingStore.getState()
    store.addNegotiationEvent(status("started"))

    store.reset()

    expect(useGroupStreamingStore.getState().negotiationEvents).toEqual([])
  })

  it("does not touch the logistics events", () => {
    useGroupStreamingStore.getState().addNegotiationEvent(status("started"))

    expect(useGroupStreamingStore.getState().events).toEqual([])
  })
})
