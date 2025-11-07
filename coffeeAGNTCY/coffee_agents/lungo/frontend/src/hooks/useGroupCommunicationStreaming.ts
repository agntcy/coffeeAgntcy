/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useState, useRef, useCallback } from "react"
import { LogisticsStreamStep } from "@/types/streaming"

const DEFAULT_LOGISTICS_APP_API_URL = "http://127.0.0.1:9090"
const LOGISTICS_APP_API_URL =
  import.meta.env.VITE_LOGISTICS_APP_API_URL || DEFAULT_LOGISTICS_APP_API_URL

interface StreamingState {
  isStreaming: boolean
  events: LogisticsStreamStep[]
  finalResponse: string | null
  currentOrderId: string | null
  error: string | null
  isComplete: boolean
}

interface UseGroupCommunicationStreamingReturn {
  state: StreamingState
  startStreaming: (prompt: string) => Promise<void>
  clearState: () => void
}

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

export const useGroupCommunicationStreaming =
  (): UseGroupCommunicationStreamingReturn => {
    const [state, setState] = useState<StreamingState>({
      isStreaming: false,
      events: [],
      finalResponse: null,
      currentOrderId: null,
      error: null,
      isComplete: false,
    })

    const abortControllerRef = useRef<AbortController | null>(null)

    const clearState = useCallback(() => {
      setState({
        isStreaming: false,
        events: [],
        finalResponse: null,
        currentOrderId: null,
        error: null,
        isComplete: false,
      })
    }, [])

    const startStreaming = useCallback(
      async (prompt: string) => {
        if (abortControllerRef.current) {
          abortControllerRef.current.abort()
        }

        clearState()

        const controller = new AbortController()
        abortControllerRef.current = controller

        setState((prev) => ({ ...prev, isStreaming: true }))

        try {
          const response = await fetch(
            `${LOGISTICS_APP_API_URL}/agent/prompt/stream`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({ prompt }),
              signal: controller.signal,
            },
          )

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`)
          }

          const reader = response.body?.getReader()
          if (!reader) {
            throw new Error("No response body reader available")
          }

          const decoder = new TextDecoder()
          let buffer = ""

          try {
            while (true) {
              const { done, value } = await reader.read()

              if (done) break

              buffer += decoder.decode(value, { stream: true })

              // Process JSON objects separated by }{ pattern (no newlines)
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
                          setState((prev) => ({
                            ...prev,
                            events: [...prev.events, eventObj],
                            currentOrderId: eventObj.order_id,
                          }))
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
                      setState((prev) => ({
                        ...prev,
                        finalResponse: parsed.response,
                        isComplete: true,
                        isStreaming: false,
                      }))
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

          setState((prev) => ({
            ...prev,
            isComplete: true,
            isStreaming: false,
          }))
        } catch (error) {
          if (controller.signal.aborted) {
            return
          }

          console.error("Streaming error:", error)
          setState((prev) => ({
            ...prev,
            error: error instanceof Error ? error.message : "Streaming failed",
            isStreaming: false,
            isComplete: true,
          }))
        }
      },
      [clearState],
    )

    return {
      state,
      startStreaming,
      clearState,
    }
  }
