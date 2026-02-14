/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { create } from "zustand"
import { RecruiterStreamingEvent } from "@/types/streaming"
import { getStreamingEndpointForPattern, PATTERNS } from "@/utils/patternUtils"
import { isLocalDev, parseFetchError } from "@/utils/const.ts"

const isValidRecruiterStreamingEvent = (
    data: any,
): data is { response: RecruiterStreamingEvent; session_id?: string } => {
  return (
      data &&
      typeof data === "object" &&
      data.response &&
      typeof data.response === "object" &&
      typeof data.response.event_type === "string"
  )
}

interface RecruiterStreamingStoreState {
  status: "idle" | "connecting" | "streaming" | "completed" | "error"
  error: string | null
  events: RecruiterStreamingEvent[]
  prompt: string | null
  abortController: AbortController | null
  sessionId: string | null
  finalMessage: string | null
  agentRecords: Record<string, any> | null
  evaluationResults: Record<string, any> | null
  selectedAgent: Record<string, any> | null
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
  sessionId: null,
  finalMessage: null,
  agentRecords: null,
  evaluationResults: null,
  selectedAgent: null,
}

export const useRecruiterStreamingStore = create<RecruiterStreamingStoreState>((set) => ({
  ...initialState,

  connect: async (prompt: string) => {
    const abortController = new AbortController()
    set({
      status: "connecting",
      error: null,
      prompt,
      events: [],
      abortController,
      sessionId: null,
      finalMessage: null,
      agentRecords: null,
      evaluationResults: null,
      selectedAgent: null,
    })

    try {
      const streamingUrl = getStreamingEndpointForPattern(
          PATTERNS.ON_DEMAND_DISCOVERY,
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
                if (isValidRecruiterStreamingEvent(parsedData)) {
                  const event = parsedData.response

                  if (event.event_type === "completed") {
                    set((state) => ({
                      events: [...state.events, event],
                      sessionId: parsedData.session_id || state.sessionId,
                      finalMessage: event.message,
                      agentRecords: event.agent_records !== undefined ? event.agent_records : state.agentRecords,
                      evaluationResults: event.evaluation_results || state.evaluationResults,
                      selectedAgent: event.selected_agent !== undefined ? event.selected_agent : state.selectedAgent,
                    }))
                  } else if (event.event_type === "error") {
                    set((state) => ({
                      status: "error",
                      error: event.message || "An error occurred during streaming",
                      events: [...state.events, event],
                      abortController: null,
                    }))
                  } else {
                    // status_update
                    set((state) => ({
                      events: [...state.events, event],
                      sessionId: parsedData.session_id || state.sessionId,
                      selectedAgent: event.selected_agent !== undefined ? event.selected_agent : state.selectedAgent,
                    }))
                  }
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
        console.error("Unexpected recruiter streaming error:", error)
        set({
          status: "error",
          error: "Sorry, something went wrong. Please try again.",
          abortController: null,
        })
      }
    }
  },

  disconnect: () => {
    const { abortController } = useRecruiterStreamingStore.getState()
    if (abortController) {
      abortController.abort()
    }
    set({ status: "idle", abortController: null })
  },

  reset: () => {
    const { abortController } = useRecruiterStreamingStore.getState()
    if (abortController) {
      abortController.abort()
    }
    set(initialState)
  },
}))

export const useRecruiterStreamingStatus = () =>
    useRecruiterStreamingStore((state) => state.status)

export const useRecruiterStreamingError = () =>
    useRecruiterStreamingStore((state) => state.error)

export const useRecruiterStreamingEvents = () =>
    useRecruiterStreamingStore((state) => state.events)

export const useRecruiterStreamingPrompt = () =>
    useRecruiterStreamingStore((state) => state.prompt)

export const useRecruiterStreamingSessionId = () =>
    useRecruiterStreamingStore((state) => state.sessionId)

export const useRecruiterFinalMessage = () =>
    useRecruiterStreamingStore((state) => state.finalMessage)

export const useRecruiterAgentRecords = () =>
    useRecruiterStreamingStore((state) => state.agentRecords)

export const useRecruiterEvaluationResults = () =>
    useRecruiterStreamingStore((state) => state.evaluationResults)

export const useRecruiterSelectedAgent = () =>
    useRecruiterStreamingStore((state) => state.selectedAgent)

export const useRecruiterStreamingActions = () =>
    useRecruiterStreamingStore((state) => ({
      connect: state.connect,
      disconnect: state.disconnect,
      reset: state.reset,
    }))
