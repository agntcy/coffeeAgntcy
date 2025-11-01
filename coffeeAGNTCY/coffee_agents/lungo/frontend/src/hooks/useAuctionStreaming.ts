/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useRef, useState, useCallback } from "react"
import { RETRY_CONFIG } from "@/utils/retryUtils"
import {
  AuctionStreamingSSEState,
  AuctionStreamingResponse,
} from "@/types/streaming"

const DEFAULT_AUCTION_API_URL = "http://127.0.0.1:8000"
const AUCTION_API_URL =
  import.meta.env.VITE_EXCHANGE_APP_API_URL || DEFAULT_AUCTION_API_URL

const isValidAuctionStreamingResponse = (
  data: any,
): data is AuctionStreamingResponse => {
  if (!data || typeof data !== "object") {
    return false
  }

  if (typeof data.response !== "string" || data.response.trim() === "") {
    return false
  }

  return true
}

export const useAuctionStreaming = () => {
  const [state, setState] = useState<AuctionStreamingSSEState>({
    isConnected: false,
    isConnecting: false,
    events: [],
    error: null,
    retryState: {
      retryCount: 0,
      isRetrying: false,
      lastRetryAt: null,
      nextRetryAt: null,
    },
  })

  const sseConnectionRef = useRef<any>(null)
  const retryTimeoutRef = useRef<number | null>(null)

  const clearRetryTimeout = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current)
      retryTimeoutRef.current = null
    }
  }, [])

  const clearEvents = useCallback(() => {
    setState((prev) => ({
      ...prev,
      events: [],
    }))
  }, [])

  const connect = useCallback(
    async (prompt: string) => {
      clearRetryTimeout()

      if (sseConnectionRef.current) {
        return
      }

      setState((prev) => ({
        ...prev,
        isConnecting: true,
        error: null,
        retryState: {
          ...prev.retryState,
          isRetrying: false,
        },
      }))

      try {
        const response = await fetch(`${AUCTION_API_URL}/agent/prompt/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ prompt }),
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error("No response body reader available")
        }

        sseConnectionRef.current = { reader } as any // Store reader reference

        setState((prev) => ({
          ...prev,
          isConnecting: false,
          isConnected: true,
          error: null,
          retryState: {
            retryCount: 0,
            isRetrying: false,
            lastRetryAt: null,
            nextRetryAt: null,
          },
        }))

        // Read the stream
        const decoder = new TextDecoder()
        let buffer = ""

        try {
          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split("\n")
            buffer = lines.pop() || "" // Keep incomplete line in buffer

            for (const line of lines) {
              if (line.trim()) {
                try {
                  const parsedData = JSON.parse(line)
                  if (isValidAuctionStreamingResponse(parsedData)) {
                    setState((prev) => ({
                      ...prev,
                      events: [...prev.events, parsedData],
                    }))
                  }
                } catch (parseError) {
                  console.warn("Failed to parse streaming line:", line)
                }
              }
            }
          }
        } finally {
          reader.releaseLock()
          sseConnectionRef.current = null
          setState((prev) => ({
            ...prev,
            isConnected: false,
          }))
        }
      } catch (error) {
        console.error("Streaming error:", error)
        setState((prev) => ({
          ...prev,
          isConnecting: false,
          isConnected: false,
          error: error instanceof Error ? error.message : "Connection failed",
        }))
      }
    },
    [clearRetryTimeout],
  )

  const disconnect = useCallback(() => {
    clearRetryTimeout()

    if (sseConnectionRef.current?.reader) {
      try {
        sseConnectionRef.current.reader.cancel()
      } catch (error) {
        console.warn("Error cancelling reader:", error)
      }
      sseConnectionRef.current = null
    }

    setState((prev) => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      retryState: {
        retryCount: 0,
        isRetrying: false,
        lastRetryAt: null,
        nextRetryAt: null,
      },
    }))
  }, [clearRetryTimeout])

  const manualRetry = useCallback(
    (prompt: string) => {
      setState((prev) => ({
        ...prev,
        retryState: {
          retryCount: 0,
          isRetrying: false,
          lastRetryAt: null,
          nextRetryAt: null,
        },
      }))
      connect(prompt)
    },
    [connect],
  )

  // Don't auto-connect for auction streaming - wait for prompt
  useEffect(() => {
    return () => {
      clearRetryTimeout()

      if (sseConnectionRef.current?.reader) {
        try {
          sseConnectionRef.current.reader.cancel()
        } catch (error) {
          console.warn("Error cancelling reader:", error)
        }
        sseConnectionRef.current = null
      }

      setState((prev) => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
        retryState: {
          retryCount: 0,
          isRetrying: false,
          lastRetryAt: null,
          nextRetryAt: null,
        },
      }))
    }
  }, [clearRetryTimeout])

  return {
    ...state,
    connect,
    disconnect,
    clearEvents,
    manualRetry,
  }
}
