/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState } from "react"
import { Message } from "@/types/message"
import CoffeeGraderDropdown from "./Prompts/CoffeeGraderDropdown"
import airplaneSvg from "@/assets/airplane.svg"
import CoffeePromptsDropdown from "./Prompts/CoffeePromptsDropdown"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import UserMessage from "./UserMessage"
import AgentIcon from "@/assets/Coffee_Icon.svg"
import { cn } from "@/utils/cn.ts"
import { logger } from "@/utils/logger"

interface ChatAreaProps {
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  setButtonClicked: (clicked: boolean) => void
  setAiReplied: (replied: boolean) => void
  isBottomLayout: boolean
  showCoffeeDropdown?: boolean
  showCoffeePrompts?: boolean
  onCoffeeGraderSelect?: (query: string) => void
  onDropdownSelect?: (query: string) => void
  onUserInput?: (query: string) => void
  onApiResponse?: (response: string, isError?: boolean) => void
  currentUserMessage?: string
  agentResponse?: string
  isAgentLoading?: boolean
}

const ChatArea: React.FC<ChatAreaProps> = ({
  setMessages,
  setButtonClicked,
  setAiReplied,
  isBottomLayout,
  showCoffeeDropdown = false,
  showCoffeePrompts = false,
  onDropdownSelect,
  onUserInput,
  onApiResponse,
  currentUserMessage,
  agentResponse,
  isAgentLoading,
}) => {
  const [content, setContent] = useState<string>("")
  const [loading, setLoading] = useState<boolean>(false)
  const { sendMessageWithCallback } = useAgentAPI()

  const handleDropdownQuery = (query: string) => {
    if (onDropdownSelect) {
      onDropdownSelect(query)
    }
    processMessageWithQuery(query)
  }

  const processMessageWithQuery = async (
    messageContent: string,
  ): Promise<void> => {
    if (!messageContent.trim()) return

    setContent("")
    setLoading(true)
    setButtonClicked(true)

    await sendMessageWithCallback(messageContent, setMessages, {
      onSuccess: (response) => {
        setAiReplied(true)
        if (onApiResponse) {
          onApiResponse(response, false)
        }
      },
      onError: (error) => {
        logger.apiError("/api/ask", error)
        if (onApiResponse) {
          onApiResponse("Sorry, I encountered an error.", true)
        }
      },
    })

    setLoading(false)
  }

  const processMessage = async (): Promise<void> => {
    if (onUserInput) {
      onUserInput(content)
    }
    await processMessageWithQuery(content)
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>): void => {
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
      className={cn(
        "flex w-[1120px] flex-col items-start justify-center gap-2 bg-overlay-background px-[120px] py-4",
        currentUserMessage ? "min-h-auto" : "min-h-[120px]",
      )}
    >
      {currentUserMessage && (
        <div className="mb-4 flex w-[880px] flex-col gap-3">
          <UserMessage content={currentUserMessage} />
          {(isAgentLoading || agentResponse) && (
            <div className="flex w-[880px] flex-row items-start gap-1">
              <div className="chat-avatar-container flex h-10 w-10 flex-none items-center justify-center rounded-full bg-action-background">
                <img
                  src={AgentIcon}
                  alt="Agent"
                  className="h-[22px] w-[22px]"
                />
              </div>
              <div className="flex w-[814px] flex-col items-start justify-center rounded p-1 px-2">
                <div className="whitespace-pre-wrap break-words font-inter text-sm font-normal leading-5 !text-chat-text">
                  {isAgentLoading ? (
                    <div className="animate-pulse text-accent-primary">...</div>
                  ) : (
                    agentResponse
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {showCoffeeDropdown && (
        <div className="relative z-10 flex h-9 w-[166px] flex-row items-start gap-2 p-0">
          <CoffeeGraderDropdown visible={true} onSelect={handleDropdownQuery} />
        </div>
      )}

      {showCoffeePrompts && (
        <div className="relative z-10 flex h-9 w-[166px] flex-row items-start gap-2 p-0">
          <CoffeePromptsDropdown
            visible={true}
            onSelect={handleDropdownQuery}
          />
        </div>
      )}

      <div className="flex h-11 w-[880px] flex-row items-center gap-4 p-0">
        <div className="box-border flex h-11 w-[814px] flex-row items-center rounded border border-node-background bg-chat-input-background px-0 py-[5px]">
          <div className="flex h-[34px] w-[814px] flex-row items-center gap-[10px] px-4 py-[7px]">
            <input
              className="h-5 w-[782px] border-none bg-transparent font-cisco text-[15px] font-medium leading-5 tracking-[0.005em] text-chat-text outline-none placeholder:text-chat-text placeholder:opacity-60"
              placeholder="Type a prompt to interact with the agents"
              value={content}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setContent(e.target.value)
              }
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
          </div>
        </div>
        <div className="flex h-11 w-[50px] flex-row items-start p-0">
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
  )
}

export default ChatArea
