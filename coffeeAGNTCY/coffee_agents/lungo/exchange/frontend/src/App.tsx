/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect } from "react"
import { v4 as uuid } from "uuid"
import { LOCAL_STORAGE_KEY } from "@/components/Chat/Messages"
import { logger } from "@/utils/logger"

import Navigation from "@/components/Navigation/Navigation"
import MainArea from "@/components/MainArea/MainArea"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import ChatArea from "@/components/Chat/ChatArea"
import Sidebar from "@/components/Sidebar/Sidebar"
import { Message } from "./types/message"
export const PATTERNS = {
  SLIM_A2A: "slim_a2a",
  SLIM_MULTI_A2A: "slim_multi_a2a",
} as const

export type PatternType = (typeof PATTERNS)[keyof typeof PATTERNS]

const App: React.FC = () => {
  const { sendMessage } = useAgentAPI()

  const [selectedPattern, setSelectedPattern] = useState<PatternType>(
    PATTERNS.SLIM_MULTI_A2A,
  )
  const [aiReplied, setAiReplied] = useState<boolean>(false)
  const [buttonClicked, setButtonClicked] = useState<boolean>(false)
  const [currentUserMessage, setCurrentUserMessage] = useState<string>("")
  const [agentResponse, setAgentResponse] = useState<string>("")
  const [isAgentLoading, setIsAgentLoading] = useState<boolean>(false)
  const [messages, setMessages] = useState<Message[]>(() => {
    const saved = localStorage.getItem(LOCAL_STORAGE_KEY)
    return saved
      ? JSON.parse(saved)
      : [
          {
            role: "assistant",
            content: "Hi! Select a pattern to get started.",
            id: uuid(),
            animate: false,
          },
        ]
  })

  useEffect(() => {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages))
  }, [messages])

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
      const response = await sendMessage(query)
      handleApiResponse(response, false)
    } catch (error) {
      logger.apiError("/api/ask", error)
      handleApiResponse("Sorry, I encountered an error.", true)
    }
  }

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-primary-bg">
      <Navigation />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          selectedPattern={selectedPattern}
          onPatternChange={setSelectedPattern}
        />

        <div className="flex flex-1 flex-col border-l border-[#00142B] bg-primary-bg">
          <div className="relative flex-grow">
            <MainArea
              pattern={selectedPattern}
              buttonClicked={buttonClicked}
              setButtonClicked={setButtonClicked}
              aiReplied={aiReplied}
              setAiReplied={setAiReplied}
            />
          </div>

          <div className="flex min-h-[76px] w-full flex-none flex-col items-center justify-center gap-0 bg-[#2E3E57] p-0">
            <ChatArea
              setMessages={setMessages}
              setButtonClicked={setButtonClicked}
              setAiReplied={setAiReplied}
              isBottomLayout={true}
              showCoffeeDropdown={selectedPattern === PATTERNS.SLIM_A2A}
              showCoffeePrompts={selectedPattern === PATTERNS.SLIM_MULTI_A2A}
              onCoffeeGraderSelect={handleCoffeeGraderSelect}
              onDropdownSelect={handleDropdownSelect}
              onUserInput={handleUserInput}
              onApiResponse={handleApiResponse}
              currentUserMessage={currentUserMessage}
              agentResponse={agentResponse}
              isAgentLoading={isAgentLoading}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
