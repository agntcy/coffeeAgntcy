/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState } from "react"
import { Box, Button, Icons, InputField, Stack } from "@open-ui-kit/core"
import CoffeeGraderDropdown from "./CoffeeGraderDropdown"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import UserMessage from "./UserMessage"
import ChatHeader from "./ChatHeader"
import Message from "./Message"
import { ChatAgentAvatar } from "./shared/ChatAvatarCircle"
import { LoadingDots } from "@/components/loading/LoadingDots"
import { visuallyHiddenSx } from "@/utils/a11ySx"
import { mainAreaContentHorizontalPadding } from "@/components/MainArea/mainAreaContentPadding"
import {
  chatComposerNarrowContainerQuery,
  CHAT_COMPOSER_STACKED_GAP_PX,
} from "./composer/chatComposerLayout"
import { composerPrimaryButtonSx } from "@/utils/composerPrimaryButtonSx"
import { iconGlyphFillSx } from "@/utils/iconGlyphFill"
import { transparentScrollbarSx } from "@/utils/transparentScrollbarSx"
import { Message as MessageType } from "@/types/Message"
import { logger } from "@/utils/logger"

const COMPOSER_CONTROL_HEIGHT_PX = 34

const promptsDropdownSx = {
  flexShrink: 0,
  alignSelf: "flex-end" as const,
  [chatComposerNarrowContainerQuery]: {
    alignSelf: "stretch",
  },
}

interface ChatAreaProps {
  messages: MessageType[]
  setMessages: React.Dispatch<React.SetStateAction<MessageType[]>>
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
  isMinimized?: boolean
  onMinimizedChange?: (minimized: boolean) => void
  fillHeight?: boolean
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
  isMinimized = false,
  onMinimizedChange,
  fillHeight = true,
}) => {
  const [content, setContent] = useState<string>("")
  const { loading, sendMessageWithCallback } = useAgentAPI()

  const handleMinimize = () => {
    onMinimizedChange?.(true)
  }

  const handleRestore = () => {
    onMinimizedChange?.(false)
  }

  const handleDropdownQuery = (query: string) => {
    if (isMinimized) {
      onMinimizedChange?.(false)
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
    const query = content.trim()
    if (!query || loading) {
      return
    }

    if (isMinimized) {
      onMinimizedChange?.(false)
    }

    if (onUserInput) {
      onUserInput(query)
    }
    await processMessageWithQuery(query)
    setContent("")
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      void processMessage()
    }
  }

  if (!isBottomLayout) {
    return null
  }

  return (
    <Box
      ref={chatRef}
      sx={{
        containerType: "inline-size",
        containerName: "chat",
        position: "relative",
        display: "flex",
        width: "100%",
        height: fillHeight ? "100%" : "fit-content",
        maxHeight: fillHeight ? "100%" : "none",
        minHeight: fillHeight ? 0 : "fit-content",
        flexDirection: "column",
        boxSizing: "border-box",
        overflow: "hidden",
        backgroundColor: (theme) => theme.palette.action.selected,
        ...(!fillHeight
          ? { borderTop: "1px solid", borderColor: "divider" }
          : {}),
      }}
    >
      {currentUserMessage ? (
        <>
          <Box sx={{ flexShrink: 0, width: "100%" }}>
            <ChatHeader
              onMinimize={isMinimized ? handleRestore : handleMinimize}
              onClearConversation={onClearConversation}
              isMinimized={isMinimized}
              showActions={!!agentResponse && !isAgentLoading}
            />
          </Box>
          {!isMinimized ? (
            <Box
              role="region"
              aria-label="Chat messages"
              sx={(theme) => ({
                flex: fillHeight ? "1 1 auto" : "0 0 auto",
                minHeight: fillHeight ? 0 : undefined,
                width: "100%",
                overflowY: "auto",
                overflowX: "hidden",
                scrollbarGutter: "stable both-edges",
                borderTop: "1px solid",
                borderColor: "divider",
                ...transparentScrollbarSx(theme),
              })}
            >
              <Stack
                alignItems="center"
                spacing={1}
                sx={{
                  width: "100%",
                  boxSizing: "border-box",
                  px: mainAreaContentHorizontalPadding,
                  py: 1,
                }}
              >
                <Stack spacing={1.5} sx={{ width: "100%", maxWidth: 880 }}>
                  <UserMessage content={currentUserMessage} />
                  {(isAgentLoading || agentResponse) && (
                    <Message icon={<ChatAgentAvatar />}>
                      {isAgentLoading ? (
                        <>
                          <Box component="span" sx={visuallyHiddenSx}>
                            Agent is responding
                          </Box>
                          <LoadingDots />
                        </>
                      ) : (
                        agentResponse
                      )}
                    </Message>
                  )}
                </Stack>
              </Stack>
            </Box>
          ) : null}
        </>
      ) : null}

      <Stack
        data-chat-composer-region
        alignItems="space-between"
        spacing={1}
        sx={{
          flexShrink: 0,
          width: "100%",
          boxSizing: "border-box",
          px: mainAreaContentHorizontalPadding,
          py: currentUserMessage ? 1 : 2,
          borderTop: currentUserMessage ? "1px solid" : "none",
          borderColor: "divider",
          ...(!fillHeight
            ? {
                height: "fit-content",
                minHeight: "fit-content",
              }
            : {}),
        }}
      >
        <Stack
          direction="row"
          alignItems="center"
          spacing={2}
          sx={{
            width: "100%",
            [chatComposerNarrowContainerQuery]: {
              flexDirection: "column",
              alignItems: "stretch",
              gap: `${CHAT_COMPOSER_STACKED_GAP_PX}px`,
              "& > :not(style) ~ :not(style)": {
                margin: 0,
              },
            },
          }}
        >
          <Box sx={promptsDropdownSx}>
            <CoffeeGraderDropdown
              visible={true}
              onSelect={handleDropdownQuery}
            />
          </Box>

          <InputField
            fullWidth
            size="small"
            placeholder="Type a prompt to interact with the agents"
            value={content}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setContent(e.target.value)
            }
            onKeyDown={handleKeyDown}
            disabled={loading}
            slotProps={{
              htmlInput: {
                "aria-label": "Message to agents",
              },
            }}
            sx={(theme) => ({
              "& .MuiInput-root.MuiInputBase-sizeSmall": {
                marginTop: 0,
                height: COMPOSER_CONTROL_HEIGHT_PX,
                minHeight: COMPOSER_CONTROL_HEIGHT_PX,
                borderColor: "transparent",

                "&:has(.MuiInput-input:not(:placeholder-shown))": {
                  borderColor: theme.palette.vars.interactiveTertiaryDefault,
                },
                "&:has(.MuiInput-input:not(:placeholder-shown)):hover": {
                  borderColor: theme.palette.vars.interactiveTertiaryHover,
                },
              },
            })}
          />
          <Button
            size="medium"
            type="button"
            variant="primary"
            disabled={loading || !content.trim()}
            onClick={() => {
              if (content.trim() && !loading) {
                void processMessage()
              }
            }}
            endIcon={<Icons.Send />}
            sx={(theme) => ({
              flexShrink: 0,
              alignSelf: "flex-end",
              [chatComposerNarrowContainerQuery]: {
                alignSelf: "stretch",
              },
              ...theme.typography.body1,
              ...composerPrimaryButtonSx(theme),
              "& .MuiButton-endIcon": iconGlyphFillSx(
                theme.palette.vars.baseTextInverse,
                { important: true },
              ),
            })}
          >
            Send
          </Button>
        </Stack>
      </Stack>
    </Box>
  )
}

export default ChatArea
