/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback, useEffect, useRef, useState } from "react"
import { v4 as uuid } from "uuid"
import { LUNGO_FRONTEND_URLS } from "@/urls"
import { reportRequestError } from "@/errors/request"
import type { useAppChatState, useAppStreamingState } from "@/hooks/useApp"
import { isPlaceholderWorkflow } from "@/components/Sidebar/sidebar.utils"
import type { useAgentAPI } from "@/hooks/agent"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import {
  getAgentPromptStreamUrlForWorkflow,
  isChatEnabledWorkflow,
  workflowChatTransport,
  workflowChatUiMode,
} from "@/utils/workflow"

type AppChat = ReturnType<typeof useAppChatState>
type AppStreaming = ReturnType<typeof useAppStreamingState>

interface UseAppPromptHandlersParams {
  chat: AppChat
  streaming: AppStreaming
  selectedWorkflowSummary: WorkflowSummary | null
  activeWorkflowInstanceId: string | null
  sendMessage: ReturnType<typeof useAgentAPI>["sendMessage"]
  selectedReferencePattern: string | null
  setPatternChatSessionId: (id: string | null) => void
}

export function useAppPromptHandlers({
  chat,
  streaming,
  selectedWorkflowSummary,
  activeWorkflowInstanceId,
  sendMessage,
  selectedReferencePattern,
  setPatternChatSessionId,
}: UseAppPromptHandlersParams) {
  const streamCompleteRef = useRef<boolean>(false)
  const [highlightNodeFunction, setHighlightNodeFunction] = useState<
    ((nodeId: string) => void) | null
  >(null)

  const handleSendPrompt = useCallback(
    async (query: string) => {
      chat.setCurrentUserMessage(query)
      chat.setIsAgentLoading(true)
      chat.setButtonClicked(true)
      chat.setApiErrorMessage(null)

      const transport = workflowChatTransport(selectedWorkflowSummary)
      if (
        !selectedWorkflowSummary ||
        isPlaceholderWorkflow(selectedWorkflowSummary) ||
        !isChatEnabledWorkflow(selectedWorkflowSummary) ||
        transport === null
      ) {
        chat.handleApiResponse(
          "No chat backend configured for this workflow.",
          true,
        )
        chat.setIsAgentLoading(false)
        return
      }

      const streamUrl = getAgentPromptStreamUrlForWorkflow(
        selectedWorkflowSummary,
      )

      try {
        if (transport === "group_sse") {
          chat.setExecutionKey(Date.now().toString())
          chat.setShowFinalResponse(false)
          chat.setAgentResponse(undefined)
          chat.setPendingResponse("")
          chat.setGroupCommResponseReceived(false)
          streamCompleteRef.current = false
          streaming.resetGroup()
          try {
            await streaming.startStreaming(
              query,
              activeWorkflowInstanceId,
              streamUrl,
            )
          } catch (err) {
            reportRequestError(
              LUNGO_FRONTEND_URLS.apiPaths.agentPromptStream.endpointLabel,
              err,
              {
                userMessage: "Sorry, I encountered an error with streaming.",
              },
            )
            chat.setShowFinalResponse(true)
            chat.handleApiResponse(
              "Sorry, I encountered an error with streaming.",
              true,
            )
          }
        } else if (transport === "auction_stream") {
          chat.setShowFinalResponse(false)
          chat.setShowAuctionStreaming(true)
          chat.setAgentResponse(undefined)
          streaming.reset()
          try {
            await streaming.connect(query, activeWorkflowInstanceId, streamUrl)
          } catch (err) {
            reportRequestError(
              LUNGO_FRONTEND_URLS.apiPaths.agentPromptStream.endpointLabel,
              err,
              {
                userMessage:
                  "Sorry, I encountered an error with auction streaming.",
              },
            )
            chat.setShowFinalResponse(true)
            chat.handleApiResponse(
              "Sorry, I encountered an error with auction streaming.",
              true,
            )
          }
        } else if (transport === "recruiter_stream") {
          chat.setShowFinalResponse(false)
          chat.setShowRecruiterStreaming(true)
          chat.setAgentResponse(undefined)
          const priorSessionId = streaming.recruiterSessionId
          streaming.resetRecruiter()
          try {
            await streaming.connectRecruiter(
              query,
              activeWorkflowInstanceId,
              priorSessionId,
              streamUrl,
            )
          } catch (err) {
            reportRequestError(
              LUNGO_FRONTEND_URLS.apiPaths.agentPromptStream.endpointLabel,
              err,
              {
                userMessage:
                  "Sorry, I encountered an error with recruiter streaming.",
              },
            )
            chat.setShowFinalResponse(true)
            chat.handleApiResponse(
              "Sorry, I encountered an error with recruiter streaming.",
              true,
            )
          }
        } else {
          chat.setShowFinalResponse(true)
          const response = await sendMessage(query, selectedWorkflowSummary)
          chat.handleApiResponse(response, false)
          chat.setAiReplied(true)
        }
      } catch (err) {
        reportRequestError(
          LUNGO_FRONTEND_URLS.apiPaths.agentPrompt.endpointLabel,
          err,
        )
        chat.handleApiResponse(
          err instanceof Error ? err.message : String(err),
          true,
        )
        chat.setShowProgressTracker(false)
      }
    },
    [
      activeWorkflowInstanceId,
      selectedWorkflowSummary,
      sendMessage,
      streaming,
      chat,
    ],
  )

  const handleStreamComplete = useCallback(() => {
    streamCompleteRef.current = true
    const uiMode = workflowChatUiMode(selectedWorkflowSummary)
    if (uiMode?.isGroupMessaging) {
      chat.setShowFinalResponse(true)
      chat.setIsAgentLoading(true)
      if (chat.pendingResponse) {
        const isError =
          chat.pendingResponse.includes("error") ||
          chat.pendingResponse.includes("Error")
        chat.handleApiResponse(chat.pendingResponse, isError)
        chat.setPendingResponse("")
      }
    }
  }, [selectedWorkflowSummary, chat])

  const handleClearConversation = useCallback(() => {
    chat.resetChatState()
    streaming.resetGroup()
    streaming.resetRecruiter()
    if (selectedReferencePattern !== null) {
      setPatternChatSessionId(`session://${uuid()}`)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- stable reset fns only
  }, [
    chat.resetChatState,
    streaming.resetGroup,
    streaming.resetRecruiter,
    selectedReferencePattern,
    setPatternChatSessionId,
  ])

  const handleNodeHighlightSetup = useCallback(
    (highlightFunction: (nodeId: string) => void) => {
      setHighlightNodeFunction(() => highlightFunction)
    },
    [],
  )

  const handleSenderHighlight = useCallback(
    (nodeId: string) => {
      if (highlightNodeFunction) {
        highlightNodeFunction(nodeId)
      }
    },
    [highlightNodeFunction],
  )

  useEffect(() => {
    chat.resetChatState()
    chat.setShowFinalResponse(false)
    chat.setPendingResponse("")
    const uiMode = workflowChatUiMode(selectedWorkflowSummary)
    if (uiMode?.showProgressTracker) {
      chat.setShowProgressTracker(true)
      streaming.resetGroup()
    } else {
      chat.setShowProgressTracker(false)
      chat.setShowAuctionStreaming(false)
      chat.setShowRecruiterStreaming(false)
      chat.setGroupCommResponseReceived(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only run when workflow or resetGroup identity changes
  }, [selectedWorkflowSummary, streaming.resetGroup])

  return {
    handleSendPrompt,
    handleStreamComplete,
    handleClearConversation,
    handleNodeHighlightSetup,
    handleSenderHighlight,
  }
}
