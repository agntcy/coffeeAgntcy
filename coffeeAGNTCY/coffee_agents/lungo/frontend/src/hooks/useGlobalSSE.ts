/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useRef, useState, useCallback } from "react"

const DEFAULT_HELPDESK_API_URL = "http://127.0.0.1:9094"
const HELPDESK_API_URL =
  import.meta.env.VITE_HELPDESK_API_URL || DEFAULT_HELPDESK_API_URL

export interface StreamStep {
  order_id: string
  sender: string
  receiver: string
  message: string
  timestamp: string
  state: string
  final?: boolean
}

interface SSEState {
  isConnected: boolean
  isConnecting: boolean
  events: StreamStep[]
  currentOrderId: string | null
  error: string | null
}

const isValidStreamStep = (data: any): data is StreamStep => {
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

export const useGlobalSSE = () => {
  const [state, setState] = useState<SSEState>({
    isConnected: false,
    isConnecting: false,
    events: [],
    currentOrderId: null,
    error: null,
  })

  const sseConnectionRef = useRef<EventSource | null>(null)

  const handleConnectionOpen = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isConnecting: false,
      isConnected: true,
      error: null,
    }))
  }, [])

  const handleConnectionError = useCallback((_error: Event) => {
    setState((prev) => ({
      ...prev,
      isConnecting: false,
      isConnected: false,
      error: "Connection failed",
    }))

    if (sseConnectionRef.current) {
      sseConnectionRef.current.close()
      sseConnectionRef.current = null
    }
  }, [])

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const parsedData = JSON.parse(event.data)

      if (!isValidStreamStep(parsedData)) {
        return
      }

      setState((prev) => {
        const newEvents = [...prev.events, parsedData]
        return {
          ...prev,
          events: newEvents,
          currentOrderId: parsedData.order_id,
        }
      })
    } catch (_error) {}
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
    if (sseConnectionRef.current) {
      return
    }

    setState((prev) => ({ ...prev, isConnecting: true, error: null }))

    const eventSource = new EventSource(`${HELPDESK_API_URL}/agent/chat-logs`)
    sseConnectionRef.current = eventSource

    eventSource.onopen = handleConnectionOpen
    eventSource.onmessage = handleMessage
    eventSource.onerror = handleConnectionError

    eventSource.addEventListener("switch", handleSwitch)
  }, [handleConnectionOpen, handleMessage, handleConnectionError, handleSwitch])

  const disconnect = useCallback(() => {
    if (sseConnectionRef.current) {
      sseConnectionRef.current.close()
      sseConnectionRef.current = null
      setState((prev) => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
      }))
    }
  }, [])

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
      if (sseConnectionRef.current) {
        sseConnectionRef.current.close()
        sseConnectionRef.current = null
        setState((prev) => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
        }))
      }
    }
  }, [connect])

  return {
    ...state,
    connect,
    disconnect,
    clearEvents,
  }
}
