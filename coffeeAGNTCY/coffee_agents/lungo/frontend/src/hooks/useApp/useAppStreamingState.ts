/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import {
  useStreamingStatus,
  useStreamingEvents,
  useStreamingError,
  useStreamingActions,
  useStreamingSessionId,
} from "@/stores/auctionStreamingStore"
import {
  useGroupStreamingStatus,
  useGroupFinalResponse,
  useGroupError,
  useStartGroupStreaming,
  useGroupStreamingActions,
} from "@/stores/groupStreamingStore"
import {
  useRecruiterStreamingStatus,
  useRecruiterStreamingEvents,
  useRecruiterStreamingError,
  useRecruiterStreamingActions,
  useRecruiterFinalMessage,
  useRecruiterAgentRecords,
  useRecruiterStreamingSessionId,
  useRecruiterSelectedAgent,
  useRecruiterTraceId,
  useRecruiterEvaluationResults,
} from "@/stores/recruiterStreamingStore"

/** Aggregates all streaming store state and actions for the app. */
export function useAppStreamingState() {
  const startStreaming = useStartGroupStreaming()
  const { connect, reset } = useStreamingActions()
  const status = useStreamingStatus()
  const events = useStreamingEvents()
  const error = useStreamingError()
  const sessionId = useStreamingSessionId()

  const groupStatus = useGroupStreamingStatus()
  const groupFinalResponse = useGroupFinalResponse()
  const groupError = useGroupError()
  const { reset: resetGroup } = useGroupStreamingActions()

  const recruiterStatus = useRecruiterStreamingStatus()
  const recruiterEvents = useRecruiterStreamingEvents()
  const recruiterError = useRecruiterStreamingError()
  const recruiterFinalMessage = useRecruiterFinalMessage()
  const recruiterAgentRecords = useRecruiterAgentRecords()
  const recruiterSessionId = useRecruiterStreamingSessionId()
  const recruiterTraceId = useRecruiterTraceId()
  const recruiterSelectedAgent = useRecruiterSelectedAgent()
  const recruiterEvaluationResults = useRecruiterEvaluationResults()
  const { connect: connectRecruiter, reset: resetRecruiter } =
    useRecruiterStreamingActions()

  return {
    startStreaming,
    connect,
    reset,
    status,
    events,
    error,
    sessionId,
    groupStatus,
    groupFinalResponse,
    groupError,
    resetGroup,
    recruiterStatus,
    recruiterEvents,
    recruiterError,
    recruiterFinalMessage,
    recruiterAgentRecords,
    recruiterSessionId,
    recruiterTraceId,
    recruiterSelectedAgent,
    recruiterEvaluationResults,
    connectRecruiter,
    resetRecruiter,
  }
}
