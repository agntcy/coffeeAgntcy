/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useState, useEffect, useRef, useCallback, useMemo } from "react"
import { logger } from "@/utils/logger"
import { useChatAreaMeasurement } from "@/hooks/useChatAreaMeasurement"
import { useAppStreamingState } from "@/hooks/useAppStreamingState"
import { useAppChatState } from "@/hooks/useAppChatState"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import { getGraphConfig } from "@/utils/graphConfigs"
import { PATTERNS, PatternType } from "@/utils/patternUtils"
import { DiscoveryResponseEvent } from "@/types/agent"

export type { ApiResponse } from "@/types/api"

export function useApp() {
  const { sendMessage } = useAgentAPI()
  const streaming = useAppStreamingState()

  const [selectedPattern, setSelectedPattern] = useState<PatternType>(
    PATTERNS.GROUP_COMMUNICATION,
  )

  const chat = useAppChatState({ selectedPattern })

  const streamCompleteRef = useRef<boolean>(false)
  const [discoveryResponseEvent, setDiscoveryResponseEvent] =
    useState<DiscoveryResponseEvent | null>(null)
  const lastDiscoveryKeyRef = useRef<string | null>(null)

  const [highlightNodeFunction, setHighlightNodeFunction] = useState<
    ((nodeId: string) => void) | null
  >(null)

  const handleDiscoveryResponse = useCallback((evt: DiscoveryResponseEvent) => {
    setDiscoveryResponseEvent(evt)
  }, [])

  const handlePatternChange = useCallback(
    (pattern: PatternType) => {
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
      chat.setApiError(false)
      chat.setCurrentUserMessage("")
      chat.setButtonClicked(false)
      chat.setAiReplied(false)
      setSelectedPattern(pattern)
      lastDiscoveryKeyRef.current = null
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- streaming/chat refs stable enough; full deps cause unnecessary runs
    [streaming.reset, streaming.resetRecruiter, streaming.resetGroup, chat],
  )

  useEffect(() => {
    if (selectedPattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING) {
      if (
        streaming.events.length > 0 &&
        streaming.status !== "connecting" &&
        streaming.status !== "streaming" &&
        chat.isAgentLoading
      ) {
        chat.setIsAgentLoading(false)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only run when streaming state or pattern changes
  }, [
    selectedPattern,
    streaming.events.length,
    streaming.status,
    chat.isAgentLoading,
    chat.setIsAgentLoading,
  ])

  useEffect(() => {
    if (selectedPattern === PATTERNS.GROUP_COMMUNICATION) {
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
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only run when group streaming state or pattern changes
  }, [
    selectedPattern,
    streaming.groupIsComplete,
    streaming.groupIsStreaming,
    streaming.groupFinalResponse,
    streaming.groupError,
    chat.handleApiResponse,
    chat.setShowFinalResponse,
  ])

  useEffect(() => {
    if (selectedPattern !== PATTERNS.ON_DEMAND_DISCOVERY) return

    if (streaming.recruiterStatus === "completed") {
      chat.setIsAgentLoading(false)

      if (streaming.recruiterFinalMessage) {
        chat.setShowFinalResponse(true)
        chat.handleApiResponse(
          {
            response: streaming.recruiterFinalMessage,
            session_id: streaming.recruiterSessionId ?? undefined,
          },
          false,
        )
      }

      const agentKeys = streaming.recruiterAgentRecords
        ? Object.keys(streaming.recruiterAgentRecords).sort().join(",")
        : ""
      const discoveryKey = `${streaming.recruiterSessionId ?? ""}:${agentKeys}`

      if (lastDiscoveryKeyRef.current !== discoveryKey) {
        lastDiscoveryKeyRef.current = discoveryKey
        handleDiscoveryResponse({
          response: streaming.recruiterFinalMessage ?? "",
          ts: Date.now(),
          sessionId: streaming.recruiterSessionId ?? undefined,
          agent_records: streaming.recruiterAgentRecords ?? undefined,
        })
      }
    } else if (
      streaming.recruiterStatus === "error" &&
      streaming.recruiterError
    ) {
      chat.setIsAgentLoading(false)
      chat.setShowFinalResponse(true)
      chat.handleApiResponse(
        `Streaming error: ${streaming.recruiterError}`,
        true,
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only run when recruiter streaming state or pattern changes
  }, [
    selectedPattern,
    streaming.recruiterStatus,
    streaming.recruiterFinalMessage,
    streaming.recruiterError,
    streaming.recruiterAgentRecords,
    streaming.recruiterSessionId,
    chat.handleApiResponse,
    chat.setIsAgentLoading,
    chat.setShowFinalResponse,
    handleDiscoveryResponse,
  ])

  const handleDropdownSelect = useCallback(
    async (query: string) => {
      chat.setCurrentUserMessage(query)
      chat.setIsAgentLoading(true)
      chat.setButtonClicked(true)
      chat.setApiError(false)

      try {
        if (selectedPattern === PATTERNS.GROUP_COMMUNICATION) {
          chat.setExecutionKey(Date.now().toString())
          chat.setShowFinalResponse(false)
          chat.setAgentResponse(undefined)
          chat.setPendingResponse("")
          chat.setGroupCommResponseReceived(false)
          streamCompleteRef.current = false
          streaming.resetGroup()
          try {
            await streaming.startStreaming(query)
          } catch (err) {
            logger.apiError("/agent/prompt/stream", err)
            chat.setShowFinalResponse(true)
            chat.handleApiResponse(
              "Sorry, I encountered an error with streaming.",
              true,
            )
          }
        } else if (selectedPattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING) {
          chat.setShowFinalResponse(false)
          chat.setShowAuctionStreaming(true)
          chat.setAgentResponse(undefined)
          streaming.reset()
          await streaming.connect(query)
        } else if (selectedPattern === PATTERNS.ON_DEMAND_DISCOVERY) {
          chat.setShowFinalResponse(false)
          chat.setShowRecruiterStreaming(true)
          chat.setAgentResponse(undefined)
          streaming.resetRecruiter()
          try {
            await streaming.connectRecruiter(query)
          } catch (err) {
            logger.apiError("/agent/prompt/stream", err)
            chat.setShowFinalResponse(true)
            chat.handleApiResponse(
              "Sorry, I encountered an error with recruiter streaming.",
              true,
            )
          }
        } else {
          chat.setShowFinalResponse(true)
          const response = await sendMessage(query, selectedPattern)
          chat.handleApiResponse(response, false)
        }
      } catch (err) {
        logger.apiError("/agent/prompt", err)
        chat.handleApiResponse(
          err instanceof Error ? err.message : String(err),
          true,
        )
        chat.setShowProgressTracker(false)
      }
    },
    [selectedPattern, sendMessage, streaming, chat],
  )

  const handleStreamComplete = useCallback(() => {
    streamCompleteRef.current = true
    if (selectedPattern === PATTERNS.GROUP_COMMUNICATION) {
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
  }, [selectedPattern, chat])

  const handleClearConversation = useCallback(() => {
    chat.resetChatState()
    streaming.resetGroup()
    streaming.resetRecruiter()
    lastDiscoveryKeyRef.current = null
    // eslint-disable-next-line react-hooks/exhaustive-deps -- stable reset fns only
  }, [chat.resetChatState, streaming.resetGroup, streaming.resetRecruiter])

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
    if (selectedPattern === PATTERNS.GROUP_COMMUNICATION) {
      chat.setShowProgressTracker(true)
      streaming.resetGroup()
    } else {
      chat.setShowProgressTracker(false)
      chat.setShowAuctionStreaming(false)
      chat.setShowRecruiterStreaming(false)
      chat.setGroupCommResponseReceived(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only run when pattern or resetGroup identity changes
  }, [selectedPattern, streaming.resetGroup])

  const {
    height: chatHeight,
    isExpanded,
    chatRef,
  } = useChatAreaMeasurement({ debounceMs: 100 })

  const chatHeightValue =
    chat.currentUserMessage || chat.agentResponse ? chatHeight : 76

  const graphConfig = useMemo(
    () => getGraphConfig(selectedPattern),
    [selectedPattern],
  )

  return {
    selectedPattern,
    handlePatternChange,
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
    apiError: chat.apiError,
    showProgressTracker: chat.showProgressTracker,
    showAuctionStreaming: chat.showAuctionStreaming,
    showRecruiterStreaming: chat.showRecruiterStreaming,
    showFinalResponse: chat.showFinalResponse,
    groupCommResponseReceived: chat.groupCommResponseReceived,
    discoveryResponseEvent,
    handleUserInput: chat.handleUserInput,
    handleApiResponse: chat.handleApiResponse,
    handleDropdownSelect,
    handleStreamComplete,
    handleClearConversation,
    handleNodeHighlightSetup,
    handleSenderHighlight,
    handleDiscoveryResponse,
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
  }
}
