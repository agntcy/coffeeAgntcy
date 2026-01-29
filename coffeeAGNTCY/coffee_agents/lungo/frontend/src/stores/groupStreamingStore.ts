/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { create } from "zustand"
import { LogisticsStreamStep } from "@/types/streaming"
import { isLocalDev, parseFetchError } from "@/utils/const.ts"

const DEFAULT_LOGISTICS_APP_API_URL = "http://127.0.0.1:9090"
const LOGISTICS_APP_API_URL =
    import.meta.env.VITE_LOGISTICS_APP_API_URL || DEFAULT_LOGISTICS_APP_API_URL

const isValidLogisticsStreamStep = (data: any): data is LogisticsStreamStep => {
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
  ]

  for (const field of requiredStringFields) {
    if (typeof data[field] !== "string" || data[field].trim() === "") {
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
  startStreaming: (prompt: string) => Promise<void>
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

  startStreaming: async (prompt: string) => {
    const {
      reset,
      setStreaming,
      addEvent,
      setFinalResponse,
      setComplete,
      setError,
      setSessionId,
    } = useGroupStreamingStore.getState()

    reset()
    setStreaming(true)

    try {
      const response = await fetch(
          `${LOGISTICS_APP_API_URL}/agent/prompt/stream`,
          {
            method: "POST",
            credentials: isLocalDev ? "omit" : "include",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ prompt }),
          },
      )

      if (!response.ok) {
        const { status, message } = await parseFetchError(response)

        if (status >= 400 && status < 500) {
          setError(`HTTP ${status} - ${message}`)
          setComplete(true)
          setStreaming(false)
          return
        }

        setError("Sorry, something went wrong. Please try again later.")
        setComplete(true)
        setStreaming(false)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        setError("No response body reader available")
        setComplete(true)
        setStreaming(false)
        return
      }

      const decoder = new TextDecoder()
      let buffer = ""

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          let remaining = buffer

          while (remaining.length > 0) {
            let braceCount = 0
            let jsonEnd = -1

            for (let i = 0; i < remaining.length; i++) {
              if (remaining[i] === "{") braceCount++
              else if (remaining[i] === "}") {
                braceCount--
                if (braceCount === 0) {
                  jsonEnd = i
                  break
                }
              }
            }

            if (jsonEnd === -1) {
              buffer = remaining
              break
            }

            const jsonStr = remaining.substring(0, jsonEnd + 1)
            remaining = remaining.substring(jsonEnd + 1)

            try {
              const parsed = JSON.parse(jsonStr)

              // Store session_id if present
              if (parsed.session_id && typeof parsed.session_id === "string") {
                setSessionId(parsed.session_id)
              }

              if (parsed.response && typeof parsed.response === "string") {
                if (
                    parsed.response.startsWith("{'") ||
                    parsed.response.startsWith('{"')
                ) {
                  try {
                    const jsonResponse = parsed.response
                        .replace(/'/g, '"')
                        .replace(/True/g, "true")
                        .replace(/False/g, "false")
                        .replace(/None/g, "null")

                    const eventObj = JSON.parse(jsonResponse)

                    if (isValidLogisticsStreamStep(eventObj)) {
                      addEvent(eventObj)
                    }
                  } catch (dictParseError) {
                    console.error(
                        "Error parsing dict string:",
                        dictParseError,
                        "String:",
                        parsed.response,
                    )
                  }
                } else {
                  setFinalResponse(parsed.response)
                  return
                }
              }
            } catch (parseError) {
              console.error(
                  "Error parsing JSON object:",
                  parseError,
                  "JSON:",
                  jsonStr,
              )
            }
          }

          buffer = remaining
        }
      } finally {
        reader.releaseLock()
      }

      setComplete(true)
    } catch (error) {
      console.error("Streaming error:", error)
      setError("Sorry, something went wrong. Please try again.")
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
