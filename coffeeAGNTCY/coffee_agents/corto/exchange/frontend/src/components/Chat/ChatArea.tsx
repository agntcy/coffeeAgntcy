/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState } from "react"
import airplaneSvg from "@/assets/airplane.svg"
import CoffeeGraderDropdown from "./CoffeeGraderDropdown"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import UserMessage from "./UserMessage"
import ChatHeader from "./ChatHeader"
import AgentIcon from "@/assets/Coffee_Icon.svg"
import { Message } from "@/types/Message"
import { logger } from "@/utils/logger"

interface ChatAreaProps {
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  setButtonClicked: (clicked: boolean) => void
  setAiReplied: (replied: boolean) => void
  isBottomLayout: boolean
  showCoffeeDropdown?: boolean
  onCoffeeGraderSelect?: (query: string) => void
  onDropdownSelect?: (query: string) => void
  onUserInput?: (query: string) => void
  onApiResponse?: (response: string, isError?: boolean) => void
  onClearConversation?: () => void
  currentUserMessage?: string
  agentResponse?: string
  isAgentLoading?: boolean
  chatRef?: React.RefObject<HTMLDivElement | null>
}

const ChatArea: React.FC<ChatAreaProps> = ({
  setMessages,
  setButtonClicked,
  setAiReplied,
  isBottomLayout,
  onDropdownSelect,
  onUserInput,
  onApiResponse,
  onClearConversation,
  currentUserMessage,
  agentResponse,
  isAgentLoading,
  chatRef,
}) => {
  const [content, setContent] = useState<string>("")
  const [isMinimized, setIsMinimized] = useState<boolean>(false)
  const { loading, sendMessageWithCallback } = useAgentAPI()

  const handleMinimize = () => {
    setIsMinimized(true)
  }

  const handleRestore = () => {
    setIsMinimized(false)
  }

  const handleDropdownQuery = (query: string) => {
    if (isMinimized) {
      setIsMinimized(false)
    }

    if (onDropdownSelect) {
      onDropdownSelect(query)
    }
  }

  const processMessageWithQuery = async (
    messageContent: string,
  ): Promise<void> => {
    await sendMessageWithCallback(messageContent, setMessages, {
      onStart: () => {
        setContent("")
        setButtonClicked(true)
      },
      onSuccess: (response) => {
        setAiReplied(true)
        if (onApiResponse) {
          onApiResponse(response, false)
        }
      },
      onError: (error) => {
        if (import.meta.env.DEV) {
          logger.apiError("/agent/prompt", error)
        }
        if (onApiResponse) {
          onApiResponse("Sorry, I encountered an error.", true)
        }
      },
    })
  }

  const processMessage = async (): Promise<void> => {
    if (isMinimized) {
      setIsMinimized(false)
    }

    if (onUserInput) {
      onUserInput(content)
    }
    await processMessageWithQuery(content)
    setContent("")
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      processMessage()
    }
  }

  if (!isBottomLayout) {
    return null
  }

  return (
    <div
      ref={chatRef}
      className="relative flex w-full flex-col"
      style={{ backgroundColor: "var(--overlay-background)" }}
    >
      {currentUserMessage && (
        <ChatHeader
          onMinimize={isMinimized ? handleRestore : handleMinimize}
          onClearConversation={onClearConversation}
          isMinimized={isMinimized}
          showActions={!!agentResponse && !isAgentLoading}
        />
      )}

      <div
        className={`flex w-full flex-col items-center justify-center gap-2 px-4 ${currentUserMessage ? "py-2" : "py-4"} sm:px-8 md:px-16 lg:px-[120px]`}
        style={{ minHeight: currentUserMessage ? "auto" : "120px" }}
      >
        {currentUserMessage && !isMinimized && (
          <div className="mb-4 flex w-full max-w-[880px] flex-col gap-3">
            <UserMessage content={currentUserMessage} />
            {(isAgentLoading || agentResponse) && (
              <div className="flex w-full flex-row items-start gap-1">
                <div className="chat-avatar-container flex h-10 w-10 flex-none items-center justify-center rounded-full bg-action-background">
                  <img
                    src={AgentIcon}
                    alt="Agent"
                    className="h-[22px] w-[22px]"
                  />
                </div>
                <div className="flex max-w-[calc(100%-3rem)] flex-1 flex-col items-start justify-center rounded p-1 px-2">
                  <div className="whitespace-pre-wrap break-words font-inter text-sm font-normal leading-5 !text-chat-text">
                    {isAgentLoading ? (
                      <div className="animate-pulse text-accent-primary">
                        ...
                      </div>
                    ) : (
                      agentResponse
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="relative z-10 flex h-9 w-auto w-full max-w-[880px] flex-row items-start gap-2 p-0">
          <CoffeeGraderDropdown visible={true} onSelect={handleDropdownQuery} />
        </div>

        <div className="flex w-full max-w-[880px] flex-col items-stretch gap-4 p-0 sm:flex-row sm:items-center">
          <div className="box-border flex h-11 max-w-[814px] flex-1 flex-row items-center rounded border border-node-background bg-chat-input-background px-0 py-[5px]">
            <div className="flex h-[34px] w-full flex-row items-center gap-[10px] px-4 py-[7px]">
              <input
                className="h-5 min-w-0 flex-1 border-none bg-transparent font-cisco text-[15px] font-medium leading-5 tracking-[0.005em] text-chat-text outline-none placeholder:text-chat-text placeholder:opacity-60"
                placeholder="Type a prompt to interact with the agents"
                value={content}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setContent(e.target.value)
                }
                onKeyDown={handleKeyDown}
                disabled={loading}
              />
            </div>
          </div>
          <div className="flex h-11 w-[50px] flex-none flex-row items-start p-0">
            <button
              onClick={() => {
                if (content.trim() && !loading) {
                  processMessage()
                }
              }}
              className="flex h-11 w-[50px] cursor-pointer flex-row items-center justify-center gap-[10px] rounded-md border-none bg-gradient-to-r from-[#834DD7] via-[#7670D5] to-[#58C0D0] px-4 py-[15px]"
            >
              <img src={airplaneSvg} alt="Send" className="h-[18px] w-[18px]" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatArea
