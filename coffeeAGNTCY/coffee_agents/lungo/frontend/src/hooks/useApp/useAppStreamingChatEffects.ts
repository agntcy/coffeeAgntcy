/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect } from "react"
import { NDJSON_STREAMING_STATUS } from "@/stores/ndjsonStreamingStatus"
import type { useAppChatState, useAppStreamingState } from "@/hooks/useApp"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import { workflowChatTransport } from "@/utils/workflow"

type AppChat = ReturnType<typeof useAppChatState>
type AppStreaming = ReturnType<typeof useAppStreamingState>

export function useAppStreamingChatEffects(
  selectedWorkflowSummary: WorkflowSummary | null,
  streaming: AppStreaming,
  chat: AppChat,
) {
  useEffect(() => {
    const transport = workflowChatTransport(selectedWorkflowSummary)
    if (transport !== "auction_stream") return
    if (!chat.isAgentLoading) return

    if (streaming.status === NDJSON_STREAMING_STATUS.ERROR) {
      chat.setIsAgentLoading(false)
      return
    }

    if (
      streaming.events.length > 0 &&
      streaming.status !== NDJSON_STREAMING_STATUS.CONNECTING &&
      streaming.status !== NDJSON_STREAMING_STATUS.STREAMING
    ) {
      chat.setIsAgentLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only run when streaming state or workflow changes
  }, [
    selectedWorkflowSummary,
    streaming.events.length,
    streaming.status,
    chat.isAgentLoading,
    chat.setIsAgentLoading,
  ])

  useEffect(() => {
    const transport = workflowChatTransport(selectedWorkflowSummary)
    if (transport !== "auction_stream") return

    if (streaming.status === NDJSON_STREAMING_STATUS.ERROR && streaming.error) {
      chat.setIsAgentLoading(false)
      chat.setShowFinalResponse(true)
      chat.handleApiResponse(`Streaming error: ${streaming.error}`, true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only run when auction streaming state or workflow changes
  }, [
    selectedWorkflowSummary,
    streaming.status,
    streaming.error,
    chat.handleApiResponse,
    chat.setIsAgentLoading,
    chat.setShowFinalResponse,
  ])

  useEffect(() => {
    const transport = workflowChatTransport(selectedWorkflowSummary)
    if (transport !== "group_sse") return
    if (!chat.isAgentLoading) return

    if (streaming.groupStatus === NDJSON_STREAMING_STATUS.ERROR) {
      chat.setIsAgentLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only run when group streaming state or workflow changes
  }, [
    selectedWorkflowSummary,
    streaming.groupStatus,
    chat.isAgentLoading,
    chat.setIsAgentLoading,
  ])

  useEffect(() => {
    const transport = workflowChatTransport(selectedWorkflowSummary)
    if (transport !== "group_sse") return

    if (streaming.groupStatus === NDJSON_STREAMING_STATUS.COMPLETED) {
      chat.setIsAgentLoading(false)

      if (streaming.groupFinalResponse) {
        chat.setShowFinalResponse(true)
        chat.handleApiResponse(streaming.groupFinalResponse, false)
      }
    } else if (
      streaming.groupStatus === NDJSON_STREAMING_STATUS.ERROR &&
      streaming.groupError
    ) {
      chat.setIsAgentLoading(false)
      chat.setShowFinalResponse(true)
      chat.handleApiResponse(`Streaming error: ${streaming.groupError}`, true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only run when group streaming state or workflow changes
  }, [
    selectedWorkflowSummary,
    streaming.groupStatus,
    streaming.groupFinalResponse,
    streaming.groupError,
    chat.handleApiResponse,
    chat.setIsAgentLoading,
    chat.setShowFinalResponse,
  ])

  useEffect(() => {
    const transport = workflowChatTransport(selectedWorkflowSummary)
    if (transport !== "recruiter_stream") return

    if (streaming.recruiterStatus === NDJSON_STREAMING_STATUS.COMPLETED) {
      chat.setIsAgentLoading(false)

      if (streaming.recruiterFinalMessage) {
        chat.setShowFinalResponse(true)
        chat.handleApiResponse(
          {
            response: streaming.recruiterFinalMessage,
            session_id: streaming.recruiterSessionId ?? undefined,
            trace_id: streaming.recruiterTraceId ?? undefined,
          },
          false,
        )
      }
    } else if (
      streaming.recruiterStatus === NDJSON_STREAMING_STATUS.ERROR &&
      streaming.recruiterError
    ) {
      chat.setIsAgentLoading(false)
      chat.setShowFinalResponse(true)
      chat.handleApiResponse(
        `Streaming error: ${streaming.recruiterError}`,
        true,
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only run when recruiter streaming state or workflow changes
  }, [
    selectedWorkflowSummary,
    streaming.recruiterStatus,
    streaming.recruiterFinalMessage,
    streaming.recruiterError,
    streaming.recruiterAgentRecords,
    streaming.recruiterSessionId,
    streaming.recruiterTraceId,
    chat.handleApiResponse,
    chat.setIsAgentLoading,
    chat.setShowFinalResponse,
  ])
}
