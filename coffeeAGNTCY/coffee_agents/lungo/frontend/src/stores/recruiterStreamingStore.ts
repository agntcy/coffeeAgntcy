/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { create } from "zustand"
import type { AgentRecord } from "@/types/agent"
import type { HttpRequestTarget } from "@/urls"
import type { RecruiterStreamingEvent } from "./recruiterStreaming.types"
import {
  buildPromptStreamBody,
  createAbortableNdjsonStreamingActions,
  logNdjsonLineParseWarning,
  NDJSON_STREAMING_CORE_INITIAL,
  type NdjsonStreamingCoreState,
} from "./createNdjsonStreamingStore"
import {
  NDJSON_STREAMING_STATUS,
  type NdjsonStreamingStatus,
} from "./ndjsonStreamingStatus"
import { RECRUITER_STREAM_EVENT_TYPE } from "./recruiterStreamEventType"

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

interface RecruiterStreamingStoreState extends NdjsonStreamingCoreState {
  events: RecruiterStreamingEvent[]
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

type RecruiterConnectArgs = {
  prompt: string
  workflowInstanceId?: string | null
  sessionId?: string | null
  streamRequest?: HttpRequestTarget
}

const initialState: Omit<
  RecruiterStreamingStoreState,
  "connect" | "disconnect" | "reset"
> = {
  ...NDJSON_STREAMING_CORE_INITIAL,
  events: [],
  traceId: null,
  finalMessage: null,
  agentRecords: null,
  evaluationResults: null,
  selectedAgent: null,
}

export const useRecruiterStreamingStore = create<RecruiterStreamingStoreState>(
  (set, get) => {
    const actions = createAbortableNdjsonStreamingActions<
      RecruiterStreamingStoreState,
      RecruiterConnectArgs
    >({
      get,
      set,
      initialState: initialState as RecruiterStreamingStoreState,
      guardCompletedOnError: true,
      buildConnectingPatch: (args, abortController) => ({
        status: NDJSON_STREAMING_STATUS.CONNECTING,
        error: null,
        prompt: args.prompt,
        events: [],
        abortController,
        sessionId: args.sessionId ?? null,
        traceId: null,
        finalMessage: null,
        agentRecords: null,
        evaluationResults: null,
        selectedAgent: null,
      }),
      buildRequestBody: (args) =>
        buildPromptStreamBody(args.prompt, args.workflowInstanceId, {
          ...(args.sessionId ? { session_id: args.sessionId } : {}),
        }),
      onLine: (parsedData, { set: setState }) => {
        if (!isValidRecruiterStreamingEvent(parsedData)) return

        const event = parsedData.response

        if (event.event_type === RECRUITER_STREAM_EVENT_TYPE.COMPLETED) {
          setState((state) => ({
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
          setState((state) => ({
            status: NDJSON_STREAMING_STATUS.ERROR,
            error: event.message || "An error occurred during streaming",
            events: [...state.events, event],
            abortController: null,
          }))
          return "stop"
        } else if (
          event.event_type === RECRUITER_STREAM_EVENT_TYPE.STATUS_UPDATE
        ) {
          setState((state) => ({
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
      onParseError: logNdjsonLineParseWarning,
    })

    return {
      ...initialState,
      connect: (
        prompt: string,
        workflowInstanceId?: string | null,
        sessionId?: string | null,
        streamRequest?: HttpRequestTarget,
      ) =>
        actions.connect({
          prompt,
          workflowInstanceId,
          sessionId,
          streamRequest,
        }),
      disconnect: actions.disconnect,
      reset: actions.reset,
    }
  },
)

export const useRecruiterStreamingStatus = (): NdjsonStreamingStatus =>
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
