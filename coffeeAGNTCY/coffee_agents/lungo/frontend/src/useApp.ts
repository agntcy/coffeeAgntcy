/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useState, useEffect, useRef, useCallback, useMemo } from "react"
import { v4 as uuid } from "uuid"
import { LUNGO_FRONTEND_URLS } from "@/urls"
import { reportRequestError } from "@/errors/request"
import { NDJSON_STREAMING_STATUS } from "@/stores/ndjsonStreamingStatus"
import { CanvasMode, type PatternDocState } from "@/types/patternDoc"
import {
  fetchWorkflowDocumentation,
  WorkflowDocumentationNotFoundError,
} from "@/utils/agenticWorkflowsApi"
import { useChatAreaMeasurement } from "@/hooks/useChatAreaMeasurement"
import { useAppStreamingState } from "@/hooks/useAppStreamingState"
import { useAppChatState } from "@/hooks/useAppChatState"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import { type GraphConfig } from "@/utils/graphConfigs"
import { PATTERNS, PatternType } from "@/utils/patternUtils"
import {
  AGENTIC_WORKFLOWS_CATALOG_LOG_PATH,
  fetchWorkflowSummariesWithRetry,
  pickDefaultWorkflowSummaryForPattern,
  type WorkflowSummary,
} from "@/utils/agenticWorkflowsApi"
import { useActiveWorkflowInstanceStore } from "@/stores/activeWorkflowInstanceStore"
import { isPlaceholderWorkflow } from "@/components/Sidebar/sidebar.utils"
import {
  getAgentPromptStreamUrlForWorkflow,
  getSuggestedPromptsUrlForWorkflow,
  isChatEnabledWorkflow,
  patternTypeFromSummary,
  workflowChatTransport,
  workflowChatUiMode,
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

  const [workflowCatalogSummaries, setWorkflowCatalogSummaries] = useState<
    WorkflowSummary[] | null
  >(null)
  const [workflowCatalogLoading, setWorkflowCatalogLoading] = useState(true)
  const [workflowCatalogError, setWorkflowCatalogError] = useState<
    string | null
  >(null)
  const [selectedWorkflowSummary, setSelectedWorkflowSummary] =
    useState<WorkflowSummary | null>(null)

  const [selectedReferencePattern, setSelectedReferencePattern] = useState<
    string | null
  >(null)
  const [patternChatSessionId, setPatternChatSessionId] = useState<
    string | null
  >(null)
  const [patternDocState, setPatternDocState] = useState<PatternDocState>({
    status: "idle",
    documentation: null,
    errorMessage: null,
  })

  const canvasMode: CanvasMode = useMemo(
    () =>
      selectedReferencePattern !== null
        ? CanvasMode.PATTERN_DOC
        : CanvasMode.WORKFLOW,
    [selectedReferencePattern],
  )

  const suggestedPromptsUrl = useMemo(() => {
    if (canvasMode === CanvasMode.PATTERN_DOC) return null
    return getSuggestedPromptsUrlForWorkflow(selectedWorkflowSummary)
  }, [canvasMode, selectedWorkflowSummary])

  const chat = useAppChatState({ selectedWorkflowSummary, canvasMode })

  const streamCompleteRef = useRef<boolean>(false)

  const [highlightNodeFunction, setHighlightNodeFunction] = useState<
    ((nodeId: string) => void) | null
  >(null)

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
    [streaming.reset, streaming.resetRecruiter, streaming.resetGroup, chat],
  )

  const selectReferencePattern = useCallback(
    (patternName: string | null) => {
      setSelectedReferencePattern(patternName)
      if (patternName !== null) {
        setPatternChatSessionId(`session://${uuid()}`)
        chat.resetChatState()
      } else {
        setPatternChatSessionId(null)
        setPatternDocState({
          status: "idle",
          documentation: null,
          errorMessage: null,
        })
      }
    },
    [chat],
  )

  useEffect(() => {
    if (selectedReferencePattern === null) return
    const controller = new AbortController()
    setPatternDocState({
      status: "loading",
      documentation: null,
      errorMessage: null,
    })
    fetchWorkflowDocumentation(selectedReferencePattern, controller.signal)
      .then((doc) => {
        if (controller.signal.aborted) return
        setPatternDocState({
          status: "ready",
          documentation: doc,
          errorMessage: null,
        })
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        if (err instanceof WorkflowDocumentationNotFoundError) {
          setPatternDocState({
            status: "not_found",
            documentation: null,
            errorMessage: null,
          })
        } else {
          setPatternDocState({
            status: "error",
            documentation: null,
            errorMessage: err instanceof Error ? err.message : String(err),
          })
        }
      })
    return () => controller.abort()
  }, [selectedReferencePattern])

  useEffect(() => {
    const controller = new AbortController()
    setWorkflowCatalogLoading(true)
    setWorkflowCatalogError(null)
    fetchWorkflowSummariesWithRetry(controller.signal)
      .then((rows) => {
        setWorkflowCatalogSummaries(rows)
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        const httpError = reportRequestError(
          AGENTIC_WORKFLOWS_CATALOG_LOG_PATH,
          err,
        )
        setWorkflowCatalogError(httpError.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setWorkflowCatalogLoading(false)
        }
      })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (workflowCatalogSummaries === null) return
    setSelectedWorkflowSummary((prev) => {
      if (prev) {
        const still = workflowCatalogSummaries.find((s) => s.name === prev.name)
        if (still && patternTypeFromSummary(still) === selectedPattern) {
          return still
        }
      }
      return pickDefaultWorkflowSummaryForPattern(
        workflowCatalogSummaries,
        selectedPattern,
      )
    })
  }, [workflowCatalogSummaries, selectedPattern])

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
      reportRequestError(
        LUNGO_FRONTEND_URLS.apiPaths.agentPromptStream.endpointLabel,
        new Error(streaming.error),
      )
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
    if (transport === "group_sse") {
      if (streaming.groupIsComplete && !streaming.groupIsStreaming) {
        if (streaming.groupFinalResponse) {
          chat.setShowFinalResponse(true)
          chat.handleApiResponse(streaming.groupFinalResponse, false)
        } else if (streaming.groupError) {
          const errorMsg = `Streaming error: ${streaming.groupError}`
          chat.setShowFinalResponse(true)
          chat.handleApiResponse(errorMsg, true)
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only run when group streaming state or workflow changes
  }, [
    selectedWorkflowSummary,
    streaming.groupIsComplete,
    streaming.groupIsStreaming,
    streaming.groupFinalResponse,
    streaming.groupError,
    chat.handleApiResponse,
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
    // In pattern_doc mode the server keys conversation state by session_id;
    // rotate it so a cleared chat starts a genuinely fresh backend session.
    if (selectedReferencePattern !== null) {
      setPatternChatSessionId(`session://${uuid()}`)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- stable reset fns only
  }, [
    chat.resetChatState,
    streaming.resetGroup,
    streaming.resetRecruiter,
    selectedReferencePattern,
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
    suggestedPromptsUrl,
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
