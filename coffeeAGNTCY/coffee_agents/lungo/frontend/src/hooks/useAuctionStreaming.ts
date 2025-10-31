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

  const sseConnectionRef = useRef<EventSource | null>(null)
  const retryTimeoutRef = useRef<number | null>(null)

  const clearRetryTimeout = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current)
      retryTimeoutRef.current = null
    }
  }, [])

  const handleConnectionOpen = useCallback(() => {
    clearRetryTimeout()
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
  }, [clearRetryTimeout])

  const scheduleRetry = useCallback(() => {
    setState((prev) => {
      const newRetryCount = prev.retryState.retryCount + 1

      if (newRetryCount > RETRY_CONFIG.maxRetries) {
        return {
          ...prev,
          isConnecting: false,
          isConnected: false,
          error: "Connection failed after maximum retries",
          retryState: {
            ...prev.retryState,
            isRetrying: false,
          },
        }
      }

      const delay =
        RETRY_CONFIG.baseDelay *
        Math.pow(RETRY_CONFIG.backoffMultiplier, newRetryCount - 1)
      const nextRetryAt = Date.now() + delay

      retryTimeoutRef.current = window.setTimeout(() => {
        connect()
      }, delay)

      return {
        ...prev,
        isConnecting: false,
        isConnected: false,
        error: `Connection failed, retrying in ${Math.ceil(delay / 1000)}s (${newRetryCount}/${RETRY_CONFIG.maxRetries})`,
        retryState: {
          retryCount: newRetryCount,
          isRetrying: true,
          lastRetryAt: Date.now(),
          nextRetryAt: nextRetryAt,
        },
      }
    })
  }, [])

  const handleConnectionError = useCallback(
    (_error: Event) => {
      if (sseConnectionRef.current) {
        sseConnectionRef.current.close()
        sseConnectionRef.current = null
      }

      scheduleRetry()
    },
    [scheduleRetry],
  )

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const parsedData = JSON.parse(event.data)

      if (!isValidAuctionStreamingResponse(parsedData)) {
        return
      }

      setState((prev) => {
        const newEvents = [...prev.events, parsedData]
        return {
          ...prev,
          events: newEvents,
        }
      })
    } catch (_error) {}
  }, [])

  const clearEvents = useCallback(() => {
    setState((prev) => ({
      ...prev,
      events: [],
    }))
  }, [])

  const connect = useCallback(() => {
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

    const eventSource = new EventSource(
      `${AUCTION_API_URL}/agent/prompt/stream`,
    )
    sseConnectionRef.current = eventSource

    eventSource.onopen = handleConnectionOpen
    eventSource.onmessage = handleMessage
    eventSource.onerror = handleConnectionError
  }, [
    clearRetryTimeout,
    handleConnectionOpen,
    handleMessage,
    handleConnectionError,
  ])

  const disconnect = useCallback(() => {
    clearRetryTimeout()

    if (sseConnectionRef.current) {
      sseConnectionRef.current.close()
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

  const manualRetry = useCallback(() => {
    setState((prev) => ({
      ...prev,
      retryState: {
        retryCount: 0,
        isRetrying: false,
        lastRetryAt: null,
        nextRetryAt: null,
      },
    }))
    connect()
  }, [connect])

  useEffect(() => {
    connect()

    return () => {
      clearRetryTimeout()

      if (sseConnectionRef.current) {
        sseConnectionRef.current.close()
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
  }, [connect, clearRetryTimeout])

  return {
    ...state,
    connect,
    disconnect,
    clearEvents,
    manualRetry,
  }
}
