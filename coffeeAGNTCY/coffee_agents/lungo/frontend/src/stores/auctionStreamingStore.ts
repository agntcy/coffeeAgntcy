/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { create } from "zustand"
import { AuctionStreamingResponse } from "@/types/streaming"
import { getStreamingEndpointForPattern, PATTERNS } from "@/utils/patternUtils"
import { isLocalDev, parseFetchError } from "@/utils/const.ts"

const isValidAuctionStreamingResponse = (
    data: any,
): data is AuctionStreamingResponse => {
  return (
      data &&
      typeof data === "object" &&
      typeof data.response === "string" &&
      data.response.trim() !== ""
  )
}

interface StreamingState {
  status: "idle" | "connecting" | "streaming" | "completed" | "error"
  error: string | null
  events: AuctionStreamingResponse[]
  prompt: string | null
  abortController: AbortController | null
  sessionId: string | null // <-- added
  connect: (prompt: string) => Promise<void>
  disconnect: () => void
  reset: () => void
}

const initialState = {
  status: "idle" as const,
  error: null,
  events: [],
  prompt: null,
  abortController: null,
  sessionId: null, // <-- added
}

export const useAuctionStreamingStore = create<StreamingState>((set) => ({
  ...initialState,

  connect: async (prompt: string) => {
    const abortController = new AbortController()
    set({
      status: "connecting",
      error: null,
      prompt,
      events: [],
      abortController,
      sessionId: null, // reset sessionId on new connect
    })

    try {
      const streamingUrl = getStreamingEndpointForPattern(
          PATTERNS.PUBLISH_SUBSCRIBE_STREAMING,
      )

      const response = await fetch(streamingUrl, {
        method: "POST",
        credentials: isLocalDev ? "omit" : "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
        signal: abortController.signal,
      })

      if (!response.ok) {
        const { status, message } = await parseFetchError(response)
        if (status >= 400 && status < 500) {
          set({
            status: "error",
            error: `HTTP ${status} - ${message}`,
            abortController: null,
          })
          return
        }

        set({
          status: "error",
          error: "Sorry, something went wrong. Please try again later.",
          abortController: null,
        })
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error(
            "Response body is not readable - streaming not supported",
        )
      }

      set({ status: "streaming" })

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
                  set((state) => ({
                    events: [...state.events, parsedData],
                    sessionId: parsedData.session_id || state.sessionId, // <-- update sessionId if present
                  }))
                }
              } catch (parseError) {
                console.warn("Failed to parse NDJSON line:", line, parseError)
              }
            }
          }
        }

        set({ status: "completed", abortController: null })
      } finally {
        reader.releaseLock()
      }
    } catch (error) {
      if (!abortController.signal.aborted) {
        console.error("Unexpected streaming error:", error)
        set({
          status: "error",
          error: "Sorry, something went wrong. Please try again.",
          abortController: null,
        })
      }
    }
  },

  disconnect: () => {
    const { abortController } = useAuctionStreamingStore.getState()
    if (abortController) {
      abortController.abort()
    }
    set({ status: "idle", abortController: null })
  },

  reset: () => {
    const { abortController } = useAuctionStreamingStore.getState()
    if (abortController) {
      abortController.abort()
    }
    set(initialState)
  },
}))

export const useStreamingStatus = () =>
    useAuctionStreamingStore((state) => state.status)

export const useStreamingError = () =>
    useAuctionStreamingStore((state) => state.error)

export const useStreamingEvents = () =>
    useAuctionStreamingStore((state) => state.events)

export const useStreamingPrompt = () =>
    useAuctionStreamingStore((state) => state.prompt)

export const useStreamingSessionId = () =>
    useAuctionStreamingStore((state) => state.sessionId)

export const useStreamingActions = () =>
    useAuctionStreamingStore((state) => ({
      connect: state.connect,
      disconnect: state.disconnect,
      reset: state.reset,
    }))
