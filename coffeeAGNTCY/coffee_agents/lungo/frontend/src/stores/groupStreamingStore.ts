/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { create } from "zustand"
import type { LogisticsStreamStep } from "./groupStreaming.types"
import { fetchNdjsonStream, ndjsonStreamUserMessage } from "@/api/http"
import { reportRequestError } from "@/errors/request"
import type { HttpRequestTarget } from "@/urls"
import { isLocalDev } from "@/utils/const.ts"
import { logger } from "@/utils/logger"

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
  events: LogisticsStreamStep[]
  finalResponse: string | null
  isStreaming: boolean
  isComplete: boolean
  error: string | null
  currentOrderId: string | null
  executionKey: string | null
  sessionId: string | null
}

interface LogisticsStreamingActions {
  addEvent: (event: LogisticsStreamStep) => void
  setFinalResponse: (response: string) => void
  setError: (error: string) => void
  setStreaming: (streaming: boolean) => void
  setComplete: (complete: boolean) => void
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
  events: [],
  finalResponse: null,
  isStreaming: false,
  isComplete: false,
  error: null,
  currentOrderId: null,
  executionKey: null,
  sessionId: null,
}

function handleGroupStreamPayload(
  parsed: unknown,
  actions: Pick<
    LogisticsStreamingActions,
    "addEvent" | "setFinalResponse" | "setSessionId"
  >,
): "stop" | void {
  if (!parsed || typeof parsed !== "object") return

  const record = parsed as Record<string, unknown>

  if (typeof record.session_id === "string") {
    actions.setSessionId(record.session_id)
  }

  if (typeof record.response !== "string") return

  const response = record.response

  if (response.startsWith("{'") || response.startsWith('{"')) {
    try {
      const jsonResponse = response
        .replace(/'/g, '"')
        .replace(/True/g, "true")
        .replace(/False/g, "false")
        .replace(/None/g, "null")

      const eventObj = JSON.parse(jsonResponse)

      if (isValidLogisticsStreamStep(eventObj)) {
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
>((set) => ({
  ...initialState,

  addEvent: (event: LogisticsStreamStep) =>
    set((state) => ({
      events: [...state.events, event],
      currentOrderId: event.order_id,
      isComplete: event.state === "DELIVERED" ? true : state.isComplete,
      isStreaming: event.state === "DELIVERED" ? false : state.isStreaming,
    })),

  setFinalResponse: (response: string) =>
    set({
      finalResponse: response,
      isComplete: true,
      isStreaming: false,
    }),

  setError: (error: string) =>
    set({
      error,
      isComplete: true,
      isStreaming: false,
    }),

  setStreaming: (streaming: boolean) =>
    set({
      isStreaming: streaming,
    }),

  setComplete: (complete: boolean) =>
    set({
      isComplete: complete,
      isStreaming: false,
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
      setStreaming,
      addEvent,
      setFinalResponse,
      setComplete,
      setError,
      setSessionId,
    } = useGroupStreamingStore.getState()

    if (!streamRequest?.url) {
      setError("Streaming request target is required")
      setComplete(true)
      setStreaming(false)
      return
    }

    reset()
    setStreaming(true)

    const body: { prompt: string; workflow_instance_id?: string } = { prompt }
    if (workflowInstanceId) body.workflow_instance_id = workflowInstanceId

    try {
      await fetchNdjsonStream(streamRequest.url, {
        method: "POST",
        credentials: isLocalDev ? "omit" : "include",
        endpointLabel: streamRequest.endpointLabel,
        body: JSON.stringify(body),
        splitMode: "json-objects",
        onLine: (parsed) =>
          handleGroupStreamPayload(parsed, {
            addEvent,
            setFinalResponse,
            setSessionId,
          }),
        onParseError: (jsonStr, parseError) => {
          logger.error("Error parsing JSON object:", {
            error: parseError,
            json: jsonStr,
          })
        },
      })

      setComplete(true)
    } catch (error) {
      const httpError = reportRequestError(streamRequest.endpointLabel, error)
      setError(ndjsonStreamUserMessage(httpError, "short"))
    }
  },

  reset: () => set(initialState),
}))

export const useGroupEvents = () =>
  useGroupStreamingStore((state) => state.events)

export const useGroupFinalResponse = () =>
  useGroupStreamingStore((state) => state.finalResponse)

export const useGroupIsStreaming = () =>
  useGroupStreamingStore((state) => state.isStreaming)

export const useGroupIsComplete = () =>
  useGroupStreamingStore((state) => state.isComplete)

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
    setFinalResponse: state.setFinalResponse,
    setError: state.setError,
    setStreaming: state.setStreaming,
    setComplete: state.setComplete,
    setCurrentOrderId: state.setCurrentOrderId,
    setExecutionKey: state.setExecutionKey,
    setSessionId: state.setSessionId,
    startStreaming: state.startStreaming,
    reset: state.reset,
  }))

export const useStartGroupStreaming = () =>
  useGroupStreamingStore((state) => state.startStreaming)
