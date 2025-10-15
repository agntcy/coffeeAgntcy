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
      console.warn(`Invalid or empty ${field} in stream data:`, data[field])
      return false
    }
  }

  if (data.final !== undefined && typeof data.final !== "boolean") {
    console.warn("Invalid final field in stream data:", data.final)
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
    console.log("Global SSE connection opened")
    setState((prev) => ({
      ...prev,
      isConnecting: false,
      isConnected: true,
      error: null,
    }))
  }, [])

  const handleConnectionError = useCallback((error: Event) => {
    console.error("Global SSE connection error:", error)
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
    console.log("Global SSE message received:", event.data)

    try {
      const parsedData = JSON.parse(event.data)

      if (!isValidStreamStep(parsedData)) {
        console.error("Invalid stream data structure received:", {
          received: parsedData,
          expected:
            "StreamStep with order_id, sender, receiver, message, timestamp, state (strings) and optional final (boolean)",
        })
        return
      }

      setState((prev) => ({
        ...prev,
        events: [...prev.events, parsedData],
        currentOrderId: parsedData.order_id,
      }))
    } catch (error) {
      console.error("Failed to parse SSE data as JSON:", {
        error: error,
        rawData: event.data,
      })
    }
  }, [])

  const handleHeartbeat = useCallback((_event: Event) => {
    console.log("Global SSE heartbeat received")
  }, [])

  const handleSwitch = useCallback((event: MessageEvent) => {
    console.log("Global SSE switch event received:", event.data)
    try {
      const switchData = JSON.parse(event.data)
      console.log("Switching to order:", switchData.order_id)

      setState((prev) => ({
        ...prev,
        events: [],
        currentOrderId: switchData.order_id,
      }))
    } catch (error) {
      console.error("Failed to parse switch event data:", error)
    }
  }, [])

  const connect = useCallback(() => {
    if (sseConnectionRef.current) {
      console.log("SSE already connected")
      return
    }

    console.log(
      "Establishing global SSE connection to:",
      `${HELPDESK_API_URL}/agent/chat-logs`,
    )
    setState((prev) => ({ ...prev, isConnecting: true, error: null }))

    const eventSource = new EventSource(`${HELPDESK_API_URL}/agent/chat-logs`)
    sseConnectionRef.current = eventSource

    eventSource.onopen = handleConnectionOpen
    eventSource.onmessage = handleMessage
    eventSource.onerror = handleConnectionError

    // Handle custom events
    eventSource.addEventListener("heartbeat", handleHeartbeat)
    eventSource.addEventListener("switch", handleSwitch)
  }, [
    handleConnectionOpen,
    handleMessage,
    handleConnectionError,
    handleHeartbeat,
    handleSwitch,
  ])

  const disconnect = useCallback(() => {
    if (sseConnectionRef.current) {
      console.log("Closing global SSE connection")
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
    if (sseConnectionRef.current) {
      console.log("SSE already connected")
      return
    }

    console.log(
      "Establishing global SSE connection to:",
      `${HELPDESK_API_URL}/agent/chat-logs`,
    )
    setState((prev) => ({ ...prev, isConnecting: true, error: null }))

    const eventSource = new EventSource(`${HELPDESK_API_URL}/agent/chat-logs`)
    sseConnectionRef.current = eventSource

    eventSource.onopen = handleConnectionOpen
    eventSource.onmessage = handleMessage
    eventSource.onerror = handleConnectionError

    // Handle custom events
    eventSource.addEventListener("heartbeat", handleHeartbeat)
    eventSource.addEventListener("switch", handleSwitch)

    // Cleanup on unmount
    return () => {
      if (sseConnectionRef.current) {
        console.log("Closing global SSE connection")
        sseConnectionRef.current.close()
        sseConnectionRef.current = null
        setState((prev) => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
        }))
      }
    }
  }, [
    handleConnectionOpen,
    handleMessage,
    handleConnectionError,
    handleHeartbeat,
    handleSwitch,
  ])

  return {
    ...state,
    connect,
    disconnect,
    clearEvents,
  }
}
