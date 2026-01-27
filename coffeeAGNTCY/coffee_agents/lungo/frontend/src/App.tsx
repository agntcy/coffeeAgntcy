/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useRef, useCallback } from "react"
import { LOCAL_STORAGE_KEY } from "@/components/Chat/Messages"
import { logger } from "@/utils/logger"
import { useChatAreaMeasurement } from "@/hooks/useChatAreaMeasurement"
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
import Navigation from "@/components/Navigation/Navigation"
import MainArea from "@/components/MainArea/MainArea"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import ChatArea from "@/components/Chat/ChatArea"
import Sidebar from "@/components/Sidebar/Sidebar"
import { ThemeProvider } from "@/contexts/ThemeContext"
import { Message } from "./types/message"
import { getGraphConfig } from "@/utils/graphConfigs"
import { PATTERNS, PatternType } from "@/utils/patternUtils"
import { parseApiError } from "@/utils/const.ts"

interface ApiResponse {
  response: string
  session_id?: string
}

const App: React.FC = () => {
  const { sendMessage } = useAgentAPI()

  const [selectedPattern, setSelectedPattern] = useState<PatternType>(
      PATTERNS.GROUP_COMMUNICATION,
  )

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
  const [aiReplied, setAiReplied] = useState<boolean>(false)
  const [buttonClicked, setButtonClicked] = useState<boolean>(false)
  const [currentUserMessage, setCurrentUserMessage] = useState<string>("")
  const [agentResponse, setAgentResponse] = useState<ApiResponse | undefined>(undefined)
  const [isAgentLoading, setIsAgentLoading] = useState<boolean>(false)
  const [apiError, setApiError] = useState<boolean>(false)
  const [groupCommResponseReceived, setGroupCommResponseReceived] = useState(false)
  const [highlightNodeFunction, setHighlightNodeFunction] = useState<((nodeId: string) => void) | null>(null)
  const [showProgressTracker, setShowProgressTracker] = useState<boolean>(false)
  const [showAuctionStreaming, setShowAuctionStreaming] = useState<boolean>(false)
  const [showFinalResponse, setShowFinalResponse] = useState<boolean>(false)
  const [pendingResponse, setPendingResponse] = useState<string>("")
  const [executionKey, setExecutionKey] = useState<string>("")
  const streamCompleteRef = useRef<boolean>(false)

  const handlePatternChange = useCallback(
      (pattern: PatternType) => {
        reset()
        setShowAuctionStreaming(false)
        resetGroup()
        setGroupCommResponseReceived(false)
        setShowFinalResponse(false)
        setAgentResponse(undefined)
        setPendingResponse("")
        setIsAgentLoading(false)
        setApiError(false)
        setCurrentUserMessage("")
        setButtonClicked(false)
        setAiReplied(false)
        setSelectedPattern(pattern)
      },
      [reset, resetGroup],
  )

  const [messages, setMessages] = useState<Message[]>(() => {
    const saved = localStorage.getItem(LOCAL_STORAGE_KEY)
    return saved ? JSON.parse(saved) : []
  })

  useEffect(() => {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages))
  }, [messages])

  useEffect(() => {
    if (selectedPattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING) {
      if (
          events.length > 0 &&
          status !== "connecting" &&
          status !== "streaming" &&
          isAgentLoading
      ) {
        setIsAgentLoading(false)
      }
    }
  }, [selectedPattern, events.length, status, isAgentLoading])

  useEffect(() => {
    setButtonClicked(false)
    setAiReplied(false)
  }, [selectedPattern])

  const {
    height: chatHeight,
    isExpanded,
    chatRef,
  } = useChatAreaMeasurement({
    debounceMs: 100,
  })

  const chatHeightValue = currentUserMessage || agentResponse ? chatHeight : 76

  const handleUserInput = (query: string) => {
    setCurrentUserMessage(query)
    setIsAgentLoading(true)
    setButtonClicked(true)
    setApiError(false)
    if (
        selectedPattern !== PATTERNS.GROUP_COMMUNICATION &&
        selectedPattern !== PATTERNS.PUBLISH_SUBSCRIBE_STREAMING
    ) {
      setShowFinalResponse(true)
    }
  }

  // Accepts ApiResponse or string (for error fallback), but always sets ApiResponse
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
      [selectedPattern, setMessages],
  )

  useEffect(() => {
    if (selectedPattern === PATTERNS.GROUP_COMMUNICATION) {
      if (groupIsComplete && !groupIsStreaming) {
        if (groupFinalResponse) {
          setShowFinalResponse(true)
          handleApiResponse(groupFinalResponse, false)
        } else if (groupError) {
          const errorMsg = `Streaming error: ${groupError}`
          setShowFinalResponse(true)
          handleApiResponse(errorMsg, true)
        }
      }
    }
  }, [
    selectedPattern,
    groupIsComplete,
    groupIsStreaming,
    groupFinalResponse,
    groupError,
    handleApiResponse,
  ])

  const handleDropdownSelect = async (query: string) => {
    setCurrentUserMessage(query)
    setIsAgentLoading(true)
    setButtonClicked(true)
    setApiError(false)

    try {
      if (selectedPattern === PATTERNS.GROUP_COMMUNICATION) {
        const newExecutionKey = Date.now().toString()
        setExecutionKey(newExecutionKey)
        setShowFinalResponse(false)
        setAgentResponse(undefined)
        setPendingResponse("")
        setGroupCommResponseReceived(false)
        streamCompleteRef.current = false
        resetGroup()
        try {
          await startStreaming(query)
        } catch (error) {
          logger.apiError("/agent/prompt/stream", error)
          const errorMsg = "Sorry, I encountered an error with streaming."
          setShowFinalResponse(true)
          handleApiResponse(errorMsg, true)
        }
      } else if (selectedPattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING) {
        setShowFinalResponse(false)
        setShowAuctionStreaming(true)
        setAgentResponse(undefined)
        reset()
        await connect(query)
      } else {
        setShowFinalResponse(true)
        const response = await sendMessage(query, selectedPattern)
        handleApiResponse(response, false)
      }
    } catch (error) {
      logger.apiError("/agent/prompt", error)
      const errMessage = error instanceof Error ? error.message : String(error)
      handleApiResponse(errMessage, true)
      setShowProgressTracker(false)
    }
  }

  const handleStreamComplete = () => {
    streamCompleteRef.current = true
    if (selectedPattern === PATTERNS.GROUP_COMMUNICATION) {
      setShowFinalResponse(true)
      setIsAgentLoading(true)
      if (pendingResponse) {
        const isError =
            pendingResponse.includes("error") || pendingResponse.includes("Error")
        handleApiResponse(pendingResponse, isError)
        setPendingResponse("")
      }
    }
  }

  const handleClearConversation = () => {
    setMessages([])
    setCurrentUserMessage("")
    setAgentResponse(undefined)
    setIsAgentLoading(false)
    setButtonClicked(false)
    setAiReplied(false)
    setGroupCommResponseReceived(false)
    setShowFinalResponse(false)
    setPendingResponse("")
    resetGroup()
  }

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
    setCurrentUserMessage("")
    setAgentResponse(undefined)
    setIsAgentLoading(false)
    setButtonClicked(false)
    setAiReplied(false)
    setShowFinalResponse(false)
    setPendingResponse("")
    if (selectedPattern === PATTERNS.GROUP_COMMUNICATION) {
      setShowProgressTracker(true)
      resetGroup()
    } else {
      setShowProgressTracker(false)
      setShowAuctionStreaming(false)
      setGroupCommResponseReceived(false)
    }
  }, [selectedPattern, resetGroup])

  return (
      <ThemeProvider>
        <div className="bg-primary-bg flex h-screen w-screen flex-col overflow-hidden">
          <Navigation />
          <div className="flex flex-1 overflow-hidden">
            <Sidebar
                selectedPattern={selectedPattern}
                onPatternChange={handlePatternChange}
            />
            <div className="flex flex-1 flex-col border-l border-action-background bg-app-background">
              <div className="relative flex-grow">
                <MainArea
                    pattern={selectedPattern}
                    buttonClicked={buttonClicked}
                    setButtonClicked={setButtonClicked}
                    aiReplied={aiReplied}
                    setAiReplied={setAiReplied}
                    chatHeight={chatHeightValue}
                    isExpanded={isExpanded}
                    groupCommResponseReceived={groupCommResponseReceived}
                    onNodeHighlight={handleNodeHighlightSetup}
                />
              </div>
              <div className="flex min-h-[76px] w-full flex-none flex-col items-center justify-center gap-0 bg-overlay-background p-0 md:min-h-[96px]">
                <ChatArea
                    setMessages={setMessages}
                    setButtonClicked={setButtonClicked}
                    setAiReplied={setAiReplied}
                    isBottomLayout={true}
                    showCoffeePrompts={
                        selectedPattern === PATTERNS.PUBLISH_SUBSCRIBE ||
                        selectedPattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING
                    }
                    showLogisticsPrompts={
                        selectedPattern === PATTERNS.GROUP_COMMUNICATION
                    }
                    showProgressTracker={showProgressTracker}
                    showAuctionStreaming={showAuctionStreaming}
                    showFinalResponse={showFinalResponse}
                    onStreamComplete={handleStreamComplete}
                    onSenderHighlight={handleSenderHighlight}
                    pattern={selectedPattern}
                    graphConfig={getGraphConfig(
                        selectedPattern,
                        groupCommResponseReceived,
                    )}
                    onDropdownSelect={handleDropdownSelect}
                    onUserInput={handleUserInput}
                    onApiResponse={handleApiResponse}
                    onClearConversation={handleClearConversation}
                    currentUserMessage={currentUserMessage}
                    agentResponse={agentResponse}
                    executionKey={executionKey}
                    isAgentLoading={isAgentLoading}
                    apiError={apiError}
                    chatRef={chatRef}
                    auctionState={{
                      events,
                      status,
                      error,
                    }}
                />
              </div>
            </div>
          </div>
        </div>
      </ThemeProvider>
  )
}

export default App