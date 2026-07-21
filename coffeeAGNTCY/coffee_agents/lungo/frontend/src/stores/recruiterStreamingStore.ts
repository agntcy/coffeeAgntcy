/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { create } from "zustand"
import type { AgentRecord } from "@/types/agent"
import type { RecruiterStreamingEvent } from "./recruiterStreaming.types"
import {
  NDJSON_STREAMING_STATUS,
  type NdjsonStreamingStatus,
} from "./ndjsonStreamingStatus"
import { RECRUITER_STREAM_EVENT_TYPE } from "./recruiterStreamEventType"
import { fetchNdjsonStream, ndjsonStreamUserMessage } from "@/api/http"
import { reportRequestError } from "@/errors/request"
import type { HttpRequestTarget } from "@/urls"
import { isLocalDev } from "@/utils/const.ts"
import { logger } from "@/utils/logger"

const isValidRecruiterStreamingEvent = (
  data: unknown,
): data is {
  response: RecruiterStreamingEvent
  session_id?: string
  trace_id?: string
} => {
  if (!data || typeof data !== "object" || !("response" in data)) return false
  const res = (data as { response: unknown }).response
  return (
    res !== null &&
    typeof res === "object" &&
    "event_type" in res &&
    typeof (res as RecruiterStreamingEvent).event_type === "string"
  )
}

interface RecruiterStreamingStoreState {
  status: NdjsonStreamingStatus
  error: string | null
  events: RecruiterStreamingEvent[]
  prompt: string | null
  abortController: AbortController | null
  sessionId: string | null
  traceId: string | null
  finalMessage: string | null
  agentRecords: Record<string, AgentRecord> | null
  evaluationResults: Record<string, unknown> | null
  selectedAgent: Record<string, unknown> | null
  connect: (
    prompt: string,
    workflowInstanceId?: string | null,
    sessionId?: string | null,
    streamRequest?: HttpRequestTarget,
  ) => Promise<void>
  disconnect: () => void
  reset: () => void
}

const initialState = {
  status: NDJSON_STREAMING_STATUS.IDLE,
  error: null,
  events: [],
  prompt: null,
  abortController: null,
  sessionId: null,
  traceId: null,
  finalMessage: null,
  agentRecords: null,
  evaluationResults: null,
  selectedAgent: null,
}

export const useRecruiterStreamingStore = create<RecruiterStreamingStoreState>(
  (set) => ({
    ...initialState,

    connect: async (
      prompt: string,
      workflowInstanceId?: string | null,
      sessionId?: string | null,
      streamRequest?: HttpRequestTarget,
    ) => {
      const abortController = new AbortController()

      set({
        status: NDJSON_STREAMING_STATUS.CONNECTING,
        error: null,
        prompt,
        events: [],
        abortController,
        sessionId: sessionId ?? null,
        traceId: null,
        finalMessage: null,
        agentRecords: null,
        evaluationResults: null,
        selectedAgent: null,
      })

      if (!streamRequest?.url) {
        set({
          status: NDJSON_STREAMING_STATUS.ERROR,
          error: "Streaming request target is required",
          abortController: null,
        })
        return
      }

      try {
        await fetchNdjsonStream(streamRequest.url, {
          method: "POST",
          credentials: isLocalDev ? "omit" : "include",
          endpointLabel: streamRequest.endpointLabel,
          body: JSON.stringify({
            prompt,
            ...(workflowInstanceId
              ? { workflow_instance_id: workflowInstanceId }
              : {}),
            ...(sessionId ? { session_id: sessionId } : {}),
          }),
          signal: abortController.signal,
          onStreamStart: () => {
            set({ status: NDJSON_STREAMING_STATUS.STREAMING })
          },
          onLine: (parsedData) => {
            if (!isValidRecruiterStreamingEvent(parsedData)) return

            const event = parsedData.response

            if (event.event_type === RECRUITER_STREAM_EVENT_TYPE.COMPLETED) {
              set((state) => ({
                events: [...state.events, event],
                sessionId: parsedData.session_id || state.sessionId,
                traceId: parsedData.trace_id || state.traceId,
                finalMessage: event.message,
                agentRecords:
                  event.agent_records !== undefined
                    ? event.agent_records
                    : state.agentRecords,
                evaluationResults:
                  event.evaluation_results || state.evaluationResults,
                selectedAgent:
                  event.selected_agent !== undefined
                    ? event.selected_agent
                    : state.selectedAgent,
              }))
            } else if (event.event_type === RECRUITER_STREAM_EVENT_TYPE.ERROR) {
              set((state) => ({
                status: NDJSON_STREAMING_STATUS.ERROR,
                error: event.message || "An error occurred during streaming",
                events: [...state.events, event],
                abortController: null,
              }))
              return "stop"
            } else {
              set((state) => ({
                events: [...state.events, event],
                sessionId: parsedData.session_id || state.sessionId,
                traceId: parsedData.trace_id || state.traceId,
                selectedAgent:
                  event.selected_agent !== undefined
                    ? event.selected_agent
                    : state.selectedAgent,
              }))
            }
          },
          onParseError: (line, parseError) => {
            logger.warn("Failed to parse NDJSON line:", {
              line,
              parseError,
            })
          },
        })

        if (
          useRecruiterStreamingStore.getState().status !==
          NDJSON_STREAMING_STATUS.ERROR
        ) {
          set({
            status: NDJSON_STREAMING_STATUS.COMPLETED,
            abortController: null,
          })
        }
      } catch (error) {
        if (abortController.signal.aborted) return

        const httpError = reportRequestError(streamRequest.endpointLabel, error)
        set({
          status: NDJSON_STREAMING_STATUS.ERROR,
          error: ndjsonStreamUserMessage(httpError, "short"),
          abortController: null,
        })
      }
    },

    disconnect: () => {
      const { abortController } = useRecruiterStreamingStore.getState()
      if (abortController) {
        abortController.abort()
      }
      set({ status: NDJSON_STREAMING_STATUS.IDLE, abortController: null })
    },

    reset: () => {
      const { abortController } = useRecruiterStreamingStore.getState()
      if (abortController) {
        abortController.abort()
      }
      set(initialState)
    },
  }),
)

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

export const useRecruiterTraceId = () =>
  useRecruiterStreamingStore((state) => state.traceId)

export const useRecruiterStreamingActions = () =>
  useRecruiterStreamingStore((state) => ({
    connect: state.connect,
    disconnect: state.disconnect,
    reset: state.reset,
  }))
