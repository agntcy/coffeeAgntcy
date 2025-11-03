/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useRef, useState, useCallback } from "react"
import { getStreamingEndpointForPattern, PATTERNS } from "@/utils/patternUtils"
import {
  AuctionStreamingState,
  AuctionStreamingResponse,
} from "@/types/streaming"

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
  const [state, setState] = useState<AuctionStreamingState>({
    isConnected: false,
    isConnecting: false,
    events: [],
    error: null,
  })

  const streamConnectionRef =
    useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null)

  const clearEvents = useCallback(() => {
    setState((prev) => ({
      ...prev,
      events: [],
    }))
  }, [])

  const connect = useCallback(async (prompt: string) => {
    if (streamConnectionRef.current) {
      return
    }

    setState((prev) => ({
      ...prev,
      isConnecting: true,
      error: null,
    }))

    try {
      const streamingUrl = getStreamingEndpointForPattern(
        PATTERNS.PUBLISH_SUBSCRIBE_STREAMING,
      )
      const response = await fetch(streamingUrl, {
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

      streamConnectionRef.current = reader

      setState((prev) => ({
        ...prev,
        isConnecting: false,
        isConnected: true,
        error: null,
      }))

      const decoder = new TextDecoder()
      let buffer = ""

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split("\n")
          buffer = lines.pop() || ""

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
        streamConnectionRef.current = null
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
  }, [])

  const disconnect = useCallback(() => {
    if (streamConnectionRef.current) {
      try {
        streamConnectionRef.current.cancel()
      } catch (error) {
        console.warn("Error cancelling reader:", error)
      }
      streamConnectionRef.current = null
    }

    setState((prev) => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
    }))
  }, [])

  useEffect(() => {
    return () => {
      if (streamConnectionRef.current) {
        try {
          streamConnectionRef.current.cancel()
        } catch (error) {
          console.warn("Error cancelling reader:", error)
        }
        streamConnectionRef.current = null
      }
    }
  }, [])

  return {
    ...state,
    connect,
    disconnect,
    clearEvents,
  }
}
