/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import {
  useStreamingStatus,
  useStreamingEvents,
  useStreamingError,
  useStreamingActions,
} from "@/stores/auctionStreamingStore"
import {
  useGroupIsStreaming,
  useGroupIsComplete,
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
  useRecruiterEvaluationResults,
} from "@/stores/recruiterStreamingStore"

/** Aggregates all streaming store state and actions for the app. */
export function useAppStreamingState() {
  const startStreaming = useStartGroupStreaming()
  const { connect, reset } = useStreamingActions()
  const status = useStreamingStatus()
  const events = useStreamingEvents()
  const error = useStreamingError()

  const groupIsStreaming = useGroupIsStreaming()
  const groupIsComplete = useGroupIsComplete()
  const groupFinalResponse = useGroupFinalResponse()
  const groupError = useGroupError()
  const { reset: resetGroup } = useGroupStreamingActions()

  const recruiterStatus = useRecruiterStreamingStatus()
  const recruiterEvents = useRecruiterStreamingEvents()
  const recruiterError = useRecruiterStreamingError()
  const recruiterFinalMessage = useRecruiterFinalMessage()
  const recruiterAgentRecords = useRecruiterAgentRecords()
  const recruiterSessionId = useRecruiterStreamingSessionId()
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
    groupIsStreaming,
    groupIsComplete,
    groupFinalResponse,
    groupError,
    resetGroup,
    recruiterStatus,
    recruiterEvents,
    recruiterError,
    recruiterFinalMessage,
    recruiterAgentRecords,
    recruiterSessionId,
    recruiterSelectedAgent,
    recruiterEvaluationResults,
    connectRecruiter,
    resetRecruiter,
  }
}
