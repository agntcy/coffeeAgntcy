/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useState, useEffect, useCallback } from "react"
import { LOCAL_STORAGE_KEY } from "@/components/Chat/Messages"
import { PATTERNS, PatternType } from "@/utils/patternUtils"
import type { Message } from "@/components/Chat/types"
import type { ApiResponse } from "@/types/api"

export interface UseAppChatStateParams {
  selectedPattern: PatternType
}

/** Safe read of persisted messages; invalid JSON or non-array is treated as no messages. */
function getInitialMessages(): Message[] {
  try {
    const saved = localStorage.getItem(LOCAL_STORAGE_KEY)
    if (!saved) return []
    const parsed: unknown = JSON.parse(saved)
    return Array.isArray(parsed) ? (parsed as Message[]) : []
  } catch {
    return []
  }
}

/** Chat UI state, messages persistence, and response/input handlers. */
export function useAppChatState({ selectedPattern }: UseAppChatStateParams) {
  const [messages, setMessages] = useState<Message[]>(getInitialMessages)

  const [aiReplied, setAiReplied] = useState<boolean>(false)
  const [buttonClicked, setButtonClicked] = useState<boolean>(false)
  const [currentUserMessage, setCurrentUserMessage] = useState<string>("")
  const [agentResponse, setAgentResponse] = useState<ApiResponse | undefined>(
    undefined,
  )
  const [isAgentLoading, setIsAgentLoading] = useState<boolean>(false)
  const [apiError, setApiError] = useState<boolean>(false)
  const [groupCommResponseReceived, setGroupCommResponseReceived] =
    useState(false)
  const [showProgressTracker, setShowProgressTracker] = useState<boolean>(false)
  const [showAuctionStreaming, setShowAuctionStreaming] =
    useState<boolean>(false)
  const [showRecruiterStreaming, setShowRecruiterStreaming] =
    useState<boolean>(false)
  const [showFinalResponse, setShowFinalResponse] = useState<boolean>(false)
  const [pendingResponse, setPendingResponse] = useState<string>("")
  const [executionKey, setExecutionKey] = useState<string>("")

  useEffect(() => {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages))
  }, [messages])

  useEffect(() => {
    setButtonClicked(false)
    setAiReplied(false)
  }, [selectedPattern])

  const handleApiResponse = useCallback(
    (response: ApiResponse | string, isError: boolean = false) => {
      let apiResp: ApiResponse
      if (typeof response === "string") {
        apiResp = { response }
      } else {
        apiResp = response
      }
      setAgentResponse(apiResp)
      setIsAgentLoading(false)

      if (selectedPattern === PATTERNS.GROUP_COMMUNICATION) {
        setApiError(isError)
        if (!isError) {
          setGroupCommResponseReceived(true)
        }
      }

      setMessages((prev) => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: apiResp.response,
          animate: !isError,
        }
        return updated
      })
    },
    [selectedPattern],
  )

  const handleUserInput = useCallback(
    (query: string) => {
      setCurrentUserMessage(query)
      setIsAgentLoading(true)
      setButtonClicked(true)
      setApiError(false)
      if (
        selectedPattern !== PATTERNS.GROUP_COMMUNICATION &&
        selectedPattern !== PATTERNS.PUBLISH_SUBSCRIBE_STREAMING &&
        selectedPattern !== PATTERNS.ON_DEMAND_DISCOVERY
      ) {
        setShowFinalResponse(true)
      }
    },
    [selectedPattern],
  )

  const resetChatState = useCallback(() => {
    setMessages([])
    setCurrentUserMessage("")
    setAgentResponse(undefined)
    setIsAgentLoading(false)
    setButtonClicked(false)
    setAiReplied(false)
    setGroupCommResponseReceived(false)
    setShowFinalResponse(false)
    setShowRecruiterStreaming(false)
    setPendingResponse("")
  }, [])

  return {
    messages,
    setMessages,
    aiReplied,
    setAiReplied,
    buttonClicked,
    setButtonClicked,
    currentUserMessage,
    setCurrentUserMessage,
    agentResponse,
    setAgentResponse,
    isAgentLoading,
    setIsAgentLoading,
    apiError,
    setApiError,
    groupCommResponseReceived,
    setGroupCommResponseReceived,
    showProgressTracker,
    setShowProgressTracker,
    showAuctionStreaming,
    setShowAuctionStreaming,
    showRecruiterStreaming,
    setShowRecruiterStreaming,
    showFinalResponse,
    setShowFinalResponse,
    pendingResponse,
    setPendingResponse,
    executionKey,
    setExecutionKey,
    handleApiResponse,
    handleUserInput,
    resetChatState,
  }
}
