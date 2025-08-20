/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect } from "react"
import { v4 as uuid } from "uuid"
import { LOCAL_STORAGE_KEY } from "@/components/Chat/Messages"

import ChatArea from "@/components/Chat/ChatArea"

import Navigation from "@/components/Navigation/Navigation"
import MainArea from "@/components/MainArea/MainArea"
import Sidebar from "@/components/Sidebar/Sidebar"
import { Message } from "./types/Message"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import { logger } from "./utils/logger"

const App: React.FC = () => {
  const [aiReplied, setAiReplied] = useState<boolean>(false)
  const [buttonClicked, setButtonClicked] = useState<boolean>(false)
  const [currentUserMessage, setCurrentUserMessage] = useState<string>("")
  const [agentResponse, setAgentResponse] = useState<string>("")
  const [isAgentLoading, setIsAgentLoading] = useState<boolean>(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hi! How can I assist you?",
      id: uuid(),
      animate: false,
    },
  ])

  const { sendMessage } = useAgentAPI()

  useEffect(() => {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages))
  }, [messages])

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

  const handleUserInput = (query: string) => {
    setCurrentUserMessage(query)
    setIsAgentLoading(true)
  }

  const handleDropdownSelect = async (query: string) => {
    setCurrentUserMessage(query)
    setIsAgentLoading(true)

    try {
      const response = await sendMessage(query)
      handleApiResponse(response, false)
    } catch (error) {
      if (process.env.NODE_ENV === "development") {
        logger.apiError("/api/ask", error)
      }
      handleApiResponse("Sorry, I encountered an error.", true)
    }
  }

  return (
    <div className="bg-primary-bg flex h-screen w-screen flex-col overflow-hidden">
      <Navigation />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <div className="bg-primary-bg flex min-w-0 flex-1 flex-col border-l border-[#00142B]">
          <div className="relative flex-grow">
            <MainArea
              buttonClicked={buttonClicked}
              setButtonClicked={setButtonClicked}
              aiReplied={aiReplied}
              setAiReplied={setAiReplied}
            />
          </div>

          <div className="flex min-h-[76px] w-full flex-none flex-col items-center justify-center gap-0 bg-[#2E3E57] p-0 md:min-h-[96px]">
            <ChatArea
              messages={messages}
              setMessages={setMessages}
              setButtonClicked={setButtonClicked}
              setAiReplied={setAiReplied}
              isBottomLayout={true}
              showCoffeeDropdown={true}
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
