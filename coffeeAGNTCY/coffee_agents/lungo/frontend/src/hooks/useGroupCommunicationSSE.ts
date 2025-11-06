/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useRef, useState, useCallback } from "react"
import { RETRY_CONFIG } from "@/utils/retryUtils"
import { SSEState, LogisticsStreamStep } from "@/types/streaming"

const DEFAULT_HELPDESK_API_URL = "http://127.0.0.1:9094"
const HELPDESK_API_URL =
  import.meta.env.VITE_HELPDESK_API_URL || DEFAULT_HELPDESK_API_URL

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

  if (data.final !== undefined && typeof data.final !== "boolean") {
    return false
  }

  return true
}

export const useGroupCommunicationSSE = () => {
  const [state, setState] = useState<SSEState>({
    isConnected: false,
    isConnecting: false,
    events: [],
    currentOrderId: null,
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
      console.log('SSE Raw event data:', event.data)
      const parsedData = JSON.parse(event.data)
      console.log('SSE Parsed data:', parsedData)

      if (!isValidLogisticsStreamStep(parsedData)) {
        console.log('SSE Validation failed for:', parsedData)
        return
      }

      console.log('SSE Adding event to state:', parsedData)
      setState((prev) => {
        const newEvents = [...prev.events, parsedData]
        console.log('SSE New events array:', newEvents)
        return {
          ...prev,
          events: newEvents,
          currentOrderId: parsedData.order_id,
        }
      })
    } catch (error) {
      console.error('SSE Error parsing message:', error)
    }
  }, [])

  const handleSwitch = useCallback((event: MessageEvent) => {
    try {
      const switchData = JSON.parse(event.data)

      setState((prev) => ({
        ...prev,
        events: [],
        currentOrderId: switchData.order_id,
      }))
    } catch (_error) {}
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

    const eventSource = new EventSource(`${HELPDESK_API_URL}/agent/chat-logs`)
    sseConnectionRef.current = eventSource

    eventSource.onopen = handleConnectionOpen
    eventSource.onmessage = handleMessage
    eventSource.onerror = handleConnectionError

    eventSource.addEventListener("switch", handleSwitch)
  }, [
    clearRetryTimeout,
    handleConnectionOpen,
    handleMessage,
    handleConnectionError,
    handleSwitch,
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

  const clearEvents = useCallback(() => {
    setState((prev) => ({
      ...prev,
      events: [],
      currentOrderId: null,
    }))
  }, [])

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
