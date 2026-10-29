/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { create } from "zustand"
import type { HttpRequestTarget } from "@/urls"
import { logger } from "@/utils/logger"
import type { LogisticsStreamStep } from "./groupStreaming.types"
import {
  parseSupplyChainEvent,
  type SupplyChainStreamEvent,
} from "./supplyChainEvents"
import {
  buildPromptStreamBody,
  runNdjsonStreamingSession,
} from "./createNdjsonStreamingStore"
import {
  NDJSON_STREAMING_STATUS,
  type NdjsonStreamingStatus,
} from "./ndjsonStreamingStatus"

const isValidLogisticsStreamStep = (
  data: unknown,
): data is LogisticsStreamStep => {
  if (!data || typeof data !== "object") {
    return false
  }

  const requiredStringFields = [
    "order_id",
    "sender",
    "receiver",
    "message",
    "timestamp",
    "state",
  ] as const

  const obj = data as Record<string, unknown>
  for (const field of requiredStringFields) {
    const value = obj[field]
    if (typeof value !== "string" || value.trim() === "") {
      return false
    }
  }

  return true
}

interface LogisticsStreamingState {
  status: NdjsonStreamingStatus
  events: LogisticsStreamStep[]
  negotiationEvents: SupplyChainStreamEvent[]
  finalResponse: string | null
  error: string | null
  currentOrderId: string | null
  executionKey: string | null
  sessionId: string | null
}

interface LogisticsStreamingActions {
  addEvent: (event: LogisticsStreamStep) => void
  addNegotiationEvent: (event: SupplyChainStreamEvent) => void
  setFinalResponse: (response: string) => void
  setError: (error: string) => void
  setCurrentOrderId: (orderId: string) => void
  setExecutionKey: (key: string) => void
  setSessionId: (id: string) => void
  startStreaming: (
    prompt: string,
    workflowInstanceId?: string | null,
    streamRequest?: HttpRequestTarget,
  ) => Promise<void>
  reset: () => void
}

const initialState: LogisticsStreamingState = {
  status: NDJSON_STREAMING_STATUS.IDLE,
  events: [],
  negotiationEvents: [],
  finalResponse: null,
  error: null,
  currentOrderId: null,
  executionKey: null,
  sessionId: null,
}

function promoteToStreaming(
  status: NdjsonStreamingStatus,
): NdjsonStreamingStatus {
  return status === NDJSON_STREAMING_STATUS.CONNECTING
    ? NDJSON_STREAMING_STATUS.STREAMING
    : status
}

/**
 * The logistics stream sends its steps as Python-dict strings; parse those
 * leniently. Anything that is valid JSON is parsed as JSON first, so text with
 * apostrophes is never rewritten.
 */
function parseStringResponse(response: string): unknown {
  try {
    return JSON.parse(response)
  } catch {
    const jsonResponse = response
      .replace(/'/g, '"')
      .replace(/True/g, "true")
      .replace(/False/g, "false")
      .replace(/None/g, "null")
    return JSON.parse(jsonResponse)
  }
}

export function handleGroupStreamPayload(
  parsed: unknown,
  actions: Pick<
    LogisticsStreamingActions,
    "addEvent" | "addNegotiationEvent" | "setFinalResponse" | "setSessionId"
  >,
): "stop" | void {
  if (!parsed || typeof parsed !== "object") return

  const record = parsed as Record<string, unknown>

  if (typeof record.session_id === "string") {
    actions.setSessionId(record.session_id)
  }

  // Supply chain: the response is already a JSON object.
  if (record.response && typeof record.response === "object") {
    const event = parseSupplyChainEvent(record.response)
    if (event) {
      actions.addNegotiationEvent(event)
    } else {
      logger.error("Unrecognised group stream event:", {
        event: record.response,
      })
    }
    return
  }

  if (typeof record.response !== "string") return

  const response = record.response

  if (response.startsWith("{'") || response.startsWith('{"')) {
    try {
      const eventObj = parseStringResponse(response)

      const negotiationEvent = parseSupplyChainEvent(eventObj)
      if (negotiationEvent) {
        actions.addNegotiationEvent(negotiationEvent)
      } else if (isValidLogisticsStreamStep(eventObj)) {
        actions.addEvent(eventObj)
      }
    } catch (dictParseError) {
      logger.error("Error parsing dict string:", {
        error: dictParseError,
        string: response,
      })
    }
    return
  }

  actions.setFinalResponse(response)
  return "stop"
}

export const useGroupStreamingStore = create<
  LogisticsStreamingState & LogisticsStreamingActions
>((set, get) => ({
  ...initialState,

  addEvent: (event: LogisticsStreamStep) =>
    set((state) => ({
      events: [...state.events, event],
      currentOrderId: event.order_id,
      status:
        event.state === "DELIVERED"
          ? NDJSON_STREAMING_STATUS.COMPLETED
          : promoteToStreaming(state.status),
    })),

  addNegotiationEvent: (event: SupplyChainStreamEvent) =>
    set((state) => {
      const next = {
        negotiationEvents: [...state.negotiationEvents, event],
        status: promoteToStreaming(state.status),
      }
      if (event.type === "status" && event.state === "error") {
        return {
          ...next,
          error: event.message ?? "The run failed.",
          status: NDJSON_STREAMING_STATUS.ERROR,
        }
      }
      return next
    }),

  setFinalResponse: (response: string) =>
    set({
      finalResponse: response,
      status: NDJSON_STREAMING_STATUS.COMPLETED,
    }),

  setError: (error: string) =>
    set({
      error,
      status: NDJSON_STREAMING_STATUS.ERROR,
    }),

  setCurrentOrderId: (orderId: string) =>
    set({
      currentOrderId: orderId,
    }),

  setExecutionKey: (key: string) =>
    set({
      executionKey: key,
    }),

  setSessionId: (id: string) =>
    set({
      sessionId: id,
    }),

  startStreaming: async (
    prompt: string,
    workflowInstanceId?: string | null,
    streamRequest?: HttpRequestTarget,
  ) => {
    const {
      reset,
      addEvent,
      addNegotiationEvent,
      setFinalResponse,
      setError,
      setSessionId,
    } = get()

    reset()
    set({ status: NDJSON_STREAMING_STATUS.CONNECTING })

    await runNdjsonStreamingSession({
      streamRequest,
      onMissingTarget: () => setError("Streaming request target is required"),
      buildBody: () => buildPromptStreamBody(prompt, workflowInstanceId),
      splitMode: "json-objects",
      onStreamStart: () => {
        set({ status: NDJSON_STREAMING_STATUS.STREAMING })
      },
      onLine: (parsed) =>
        handleGroupStreamPayload(parsed, {
          addEvent,
          addNegotiationEvent,
          setFinalResponse,
          setSessionId,
        }),
      onParseError: (jsonStr, parseError) => {
        logger.error("Error parsing JSON object:", {
          error: parseError,
          json: jsonStr,
        })
      },
      isErrorStatus: () => get().status === NDJSON_STREAMING_STATUS.ERROR,
      onCompleted: () => {
        set({ status: NDJSON_STREAMING_STATUS.COMPLETED })
      },
      onFailed: (message) => setError(message),
    })
  },

  reset: () => set(initialState),
}))

export const useGroupEvents = () =>
  useGroupStreamingStore((state) => state.events)

export const useGroupNegotiationEvents = () =>
  useGroupStreamingStore((state) => state.negotiationEvents)

export const useGroupFinalResponse = () =>
  useGroupStreamingStore((state) => state.finalResponse)

export const useGroupStreamingStatus = () =>
  useGroupStreamingStore((state) => state.status)

export const useGroupError = () =>
  useGroupStreamingStore((state) => state.error)

export const useGroupCurrentOrderId = () =>
  useGroupStreamingStore((state) => state.currentOrderId)

export const useGroupExecutionKey = () =>
  useGroupStreamingStore((state) => state.executionKey)

export const useGroupSessionId = () =>
  useGroupStreamingStore((state) => state.sessionId)

export const useGroupStreamingActions = () =>
  useGroupStreamingStore((state) => ({
    addEvent: state.addEvent,
    addNegotiationEvent: state.addNegotiationEvent,
    setFinalResponse: state.setFinalResponse,
    setError: state.setError,
    setCurrentOrderId: state.setCurrentOrderId,
    setExecutionKey: state.setExecutionKey,
    setSessionId: state.setSessionId,
    startStreaming: state.startStreaming,
    reset: state.reset,
  }))

export const useStartGroupStreaming = () =>
  useGroupStreamingStore((state) => state.startStreaming)
