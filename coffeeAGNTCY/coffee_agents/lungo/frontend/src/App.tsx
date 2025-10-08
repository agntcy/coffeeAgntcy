/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect } from "react"
import { LOCAL_STORAGE_KEY } from "@/components/Chat/Messages"
import { logger } from "@/utils/logger"
import { useChatAreaMeasurement } from "@/hooks/useChatAreaMeasurement"

import Navigation from "@/components/Navigation/Navigation"
import MainArea from "@/components/MainArea/MainArea"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import ChatArea from "@/components/Chat/ChatArea"
import Sidebar from "@/components/Sidebar/Sidebar"
import { ThemeProvider } from "@/contexts/ThemeContext"
import { Message } from "./types/message"
export const PATTERNS = {
  SLIM_A2A: "slim_a2a",
  PUBLISH_SUBSCRIBE: "publish_subscribe",
  GROUP_COMMUNICATION: "group_communication",
} as const

export type PatternType = (typeof PATTERNS)[keyof typeof PATTERNS]

const App: React.FC = () => {
  const { sendMessage } = useAgentAPI()

  const [selectedPattern, setSelectedPattern] = useState<PatternType>(
    PATTERNS.PUBLISH_SUBSCRIBE,
  )
  const [aiReplied, setAiReplied] = useState<boolean>(false)
  const [buttonClicked, setButtonClicked] = useState<boolean>(false)
  const [currentUserMessage, setCurrentUserMessage] = useState<string>("")
  const [agentResponse, setAgentResponse] = useState<string>("")
  const [isAgentLoading, setIsAgentLoading] = useState<boolean>(false)
  const [groupCommResponseReceived, setGroupCommResponseReceived] =
    useState<boolean>(false)
  const [messages, setMessages] = useState<Message[]>(() => {
    const saved = localStorage.getItem(LOCAL_STORAGE_KEY)
    return saved ? JSON.parse(saved) : []
  })

  useEffect(() => {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages))
  }, [messages])

  const {
    height: chatHeight,
    isExpanded,
    chatRef,
  } = useChatAreaMeasurement({
    debounceMs: 100,
  })

  const chatHeightValue = currentUserMessage || agentResponse ? chatHeight : 76

  const handleCoffeeGraderSelect = (query: string) => {
    handleDropdownSelect(query)
  }

  const handleUserInput = (query: string) => {
    setCurrentUserMessage(query)
    setIsAgentLoading(true)
    setButtonClicked(true)
  }

  const handleApiResponse = (response: string, isError: boolean = false) => {
    setAgentResponse(response)
    setIsAgentLoading(false)

    if (selectedPattern === PATTERNS.GROUP_COMMUNICATION && !isError) {
      setGroupCommResponseReceived(true)
    }

    setMessages((prev) => {
      const updated = [...prev]
      updated[updated.length - 1] = {
        ...updated[updated.length - 1],
        content: response,
        animate: !isError,
      }
      return updated
    })
  }

  const handleDropdownSelect = async (query: string) => {
    setCurrentUserMessage(query)
    setIsAgentLoading(true)
    setButtonClicked(true)

    try {
      const response = await sendMessage(query, selectedPattern)
      handleApiResponse(response, false)
    } catch (error) {
      logger.apiError("/agent/prompt", error)
      handleApiResponse("Sorry, I encountered an error.", true)
    }
  }

  const handleClearConversation = () => {
    setMessages([])
    setCurrentUserMessage("")
    setAgentResponse("")
    setIsAgentLoading(false)
    setButtonClicked(false)
    setAiReplied(false)
    setGroupCommResponseReceived(false)
  }

  useEffect(() => {
    setCurrentUserMessage("")
    setAgentResponse("")
    setIsAgentLoading(false)
    setButtonClicked(false)
    setAiReplied(false)

    if (selectedPattern !== PATTERNS.GROUP_COMMUNICATION) {
      setGroupCommResponseReceived(false)
    }
  }, [selectedPattern])

  return (
    <ThemeProvider>
      <div className="bg-primary-bg flex h-screen w-screen flex-col overflow-hidden">
        <Navigation />

        <div className="flex flex-1 overflow-hidden">
          <Sidebar
            selectedPattern={selectedPattern}
            onPatternChange={setSelectedPattern}
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
              />
            </div>

            <div className="flex min-h-[76px] w-full flex-none flex-col items-center justify-center gap-0 bg-overlay-background p-0 md:min-h-[96px]">
              <ChatArea
                setMessages={setMessages}
                setButtonClicked={setButtonClicked}
                setAiReplied={setAiReplied}
                isBottomLayout={true}
                showCoffeeDropdown={selectedPattern === PATTERNS.SLIM_A2A}
                showCoffeePrompts={
                  selectedPattern === PATTERNS.PUBLISH_SUBSCRIBE
                }
                showLogisticsPrompts={
                  selectedPattern === PATTERNS.GROUP_COMMUNICATION
                }
                pattern={selectedPattern}
                onCoffeeGraderSelect={handleCoffeeGraderSelect}
                onDropdownSelect={handleDropdownSelect}
                onUserInput={handleUserInput}
                onApiResponse={handleApiResponse}
                onClearConversation={handleClearConversation}
                currentUserMessage={currentUserMessage}
                agentResponse={agentResponse}
                isAgentLoading={isAgentLoading}
                chatRef={chatRef}
              />
            </div>
          </div>
        </div>
      </div>
    </ThemeProvider>
  )
}

export default App
