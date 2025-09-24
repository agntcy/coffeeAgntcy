/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect } from "react"
import { LOCAL_STORAGE_KEY } from "@/components/Chat/Messages"

import ChatArea from "@/components/Chat/ChatArea"

import Navigation from "@/components/Navigation/Navigation"
import MainArea from "@/components/MainArea/MainArea"
import Sidebar from "@/components/Sidebar/Sidebar"
import { ThemeProvider } from "@/contexts/ThemeContext"
import { Message } from "./types/Message"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import { useChatAreaMeasurement } from "@/hooks/useChatAreaMeasurement"
import { logger } from "./utils/logger"

const App: React.FC = () => {
  const [aiReplied, setAiReplied] = useState<boolean>(false)
  const [buttonClicked, setButtonClicked] = useState<boolean>(false)
  const [currentUserMessage, setCurrentUserMessage] = useState<string>("")
  const [agentResponse, setAgentResponse] = useState<string>("")
  const [isAgentLoading, setIsAgentLoading] = useState<boolean>(false)
  const [messages, setMessages] = useState<Message[]>([])
  const { sendMessageWithCallback } = useAgentAPI()

  const {
    height: chatHeight,
    isExpanded,
    chatRef,
  } = useChatAreaMeasurement({
    debounceMs: 100,
  })

  useEffect(() => {
    const storedMessages = localStorage.getItem(LOCAL_STORAGE_KEY)
    if (storedMessages) {
      setMessages(JSON.parse(storedMessages))
    }
  }, [])

  useEffect(() => {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages))
  }, [messages])

  const chatHeightValue = currentUserMessage || agentResponse ? chatHeight : 76

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
      await sendMessageWithCallback(query, setMessages, {
        onStart: () => {
          setButtonClicked(true)
        },
        onSuccess: (response) => {
          setAiReplied(true)
          handleApiResponse(response, false)
        },
        onError: (error) => {
          if (import.meta.env.DEV) {
            logger.apiError("/agent/prompt", error)
          }
          handleApiResponse("Sorry, I encountered an error.", true)
        },
      })
    } catch (error) {
      if (import.meta.env.DEV) {
        logger.apiError("/agent/prompt", error)
      }
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
  }

  return (
    <ThemeProvider>
      <div className="flex h-screen w-screen flex-col overflow-hidden bg-app-background">
        <Navigation />

        <div className="flex flex-1 overflow-hidden">
          <Sidebar />

          <div className="flex min-w-0 flex-1 flex-col border-l border-action-background bg-app-background">
            <div className="relative flex-grow">
              <MainArea
                buttonClicked={buttonClicked}
                setButtonClicked={setButtonClicked}
                aiReplied={aiReplied}
                setAiReplied={setAiReplied}
                chatHeight={chatHeightValue}
                isExpanded={isExpanded}
              />
            </div>

            <div className="flex min-h-[76px] w-full flex-none flex-col items-center justify-center gap-0 bg-overlay-background p-0 md:min-h-[96px]">
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
