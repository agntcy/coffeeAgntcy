/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback, useMemo, useState } from "react"
import { useChatAreaMeasurement } from "@/hooks/chat"
import { useAgentAPI } from "@/hooks/agent"
import {
  useAppChatState,
  useAppPatternReference,
  useAppPromptHandlers,
  useAppStreamingChatEffects,
  useAppStreamingState,
  useAppWorkflowCatalog,
} from "@/hooks/useApp"
import { type GraphConfig } from "@/utils/graphConfigs"
import { PATTERNS, PatternType } from "@/utils/patternUtils"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import { useActiveWorkflowInstanceStore } from "@/stores/activeWorkflowInstanceStore"
import { CanvasMode } from "@/types/patternDoc"
import {
  getSuggestedPromptsRequestForWorkflow,
  patternTypeFromSummary,
} from "@/utils/workflow"

export type { ApiResponse } from "@/types/api"

export function useApp() {
  const { sendMessage } = useAgentAPI()
  const streaming = useAppStreamingState()
  const activeWorkflowInstanceId = useActiveWorkflowInstanceStore(
    (s) => s.workflowInstanceId,
  )

  const [selectedPattern, setSelectedPattern] = useState<PatternType>(
    PATTERNS.GROUP_MESSAGING,
  )
  const [liveGraphConfig, setLiveGraphConfig] = useState<GraphConfig | null>(
    null,
  )

  const {
    workflowCatalogSummaries,
    workflowCatalogLoading,
    workflowCatalogError,
    selectedWorkflowSummary,
    setSelectedWorkflowSummary,
  } = useAppWorkflowCatalog(selectedPattern)

  const {
    selectedReferencePattern,
    setSelectedReferencePattern,
    patternChatSessionId,
    setPatternChatSessionId,
    patternDocState,
    canvasMode,
    selectReferencePattern: selectReferencePatternBase,
  } = useAppPatternReference()

  const chat = useAppChatState({ selectedWorkflowSummary, canvasMode })

  const selectReferencePattern = useCallback(
    (patternName: string | null) => {
      selectReferencePatternBase(patternName)
      if (patternName !== null) {
        chat.resetChatState()
      }
    },
    [selectReferencePatternBase, chat.resetChatState],
  )

  const suggestedPromptsRequest = useMemo(() => {
    if (canvasMode === CanvasMode.PATTERN_DOC) return null
    return getSuggestedPromptsRequestForWorkflow(selectedWorkflowSummary)
  }, [canvasMode, selectedWorkflowSummary])

  useAppStreamingChatEffects(selectedWorkflowSummary, streaming, chat)

  const {
    handleSendPrompt,
    handleStreamComplete,
    handleClearConversation,
    handleNodeHighlightSetup,
    handleSenderHighlight,
  } = useAppPromptHandlers({
    chat,
    streaming,
    selectedWorkflowSummary,
    activeWorkflowInstanceId,
    sendMessage,
    selectedReferencePattern,
    setPatternChatSessionId,
  })

  const selectWorkflowFromCatalog = useCallback(
    (summary: WorkflowSummary) => {
      const slug = patternTypeFromSummary(summary)
      if (slug === null) return
      streaming.reset()
      streaming.resetRecruiter()
      chat.setShowAuctionStreaming(false)
      chat.setShowRecruiterStreaming(false)
      streaming.resetGroup()
      chat.setGroupCommResponseReceived(false)
      chat.setShowFinalResponse(false)
      chat.setAgentResponse(undefined)
      chat.setPendingResponse("")
      chat.setIsAgentLoading(false)
      chat.setApiErrorMessage(null)
      chat.setCurrentUserMessage("")
      chat.setButtonClicked(false)
      chat.setAiReplied(false)
      setSelectedPattern(slug)
      setSelectedWorkflowSummary(summary)
      setLiveGraphConfig(null)
      setSelectedReferencePattern(null)
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- streaming/chat refs stable enough; full deps cause unnecessary runs
    [
      streaming.reset,
      streaming.resetRecruiter,
      streaming.resetGroup,
      chat,
      setSelectedWorkflowSummary,
      setSelectedReferencePattern,
    ],
  )

  const {
    height: chatHeight,
    isExpanded,
    chatRef,
  } = useChatAreaMeasurement({ debounceMs: 100 })

  const chatHeightValue =
    chat.currentUserMessage || chat.agentResponse ? chatHeight : 76

  const graphConfig = useMemo(
    () => liveGraphConfig ?? undefined,
    [liveGraphConfig],
  )

  return {
    selectedPattern,
    selectWorkflowFromCatalog,
    workflowCatalogSummaries,
    workflowCatalogLoading,
    workflowCatalogError,
    selectedWorkflowSummary,
    suggestedPromptsRequest,
    chatHeightValue,
    isExpanded,
    chatRef,
    messages: chat.messages,
    setMessages: chat.setMessages,
    aiReplied: chat.aiReplied,
    setAiReplied: chat.setAiReplied,
    buttonClicked: chat.buttonClicked,
    setButtonClicked: chat.setButtonClicked,
    currentUserMessage: chat.currentUserMessage,
    agentResponse: chat.agentResponse,
    executionKey: chat.executionKey,
    isAgentLoading: chat.isAgentLoading,
    apiErrorMessage: chat.apiErrorMessage,
    showProgressTracker: chat.showProgressTracker,
    showAuctionStreaming: chat.showAuctionStreaming,
    showRecruiterStreaming: chat.showRecruiterStreaming,
    showFinalResponse: chat.showFinalResponse,
    groupCommResponseReceived: chat.groupCommResponseReceived,
    handleUserInput: chat.handleUserInput,
    handleApiResponse: chat.handleApiResponse,
    handleSendPrompt,
    handleStreamComplete,
    handleClearConversation,
    handleNodeHighlightSetup,
    handleSenderHighlight,
    graphConfig,
    events: streaming.events,
    status: streaming.status,
    error: streaming.error,
    recruiterEvents: streaming.recruiterEvents,
    recruiterStatus: streaming.recruiterStatus,
    recruiterError: streaming.recruiterError,
    recruiterSessionId: streaming.recruiterSessionId,
    recruiterFinalMessage: streaming.recruiterFinalMessage,
    recruiterAgentRecords: streaming.recruiterAgentRecords,
    recruiterEvaluationResults: streaming.recruiterEvaluationResults,
    recruiterSelectedAgent: streaming.recruiterSelectedAgent,
    setLiveGraphConfig,
    selectedReferencePattern,
    selectReferencePattern,
    canvasMode,
    patternDocState,
    patternChatSessionId,
    auctionSessionId: streaming.sessionId,
  }
}
