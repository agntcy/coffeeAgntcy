/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useRef, useState } from "react"

import { useScrollPanelOnContentResize } from "@/utils/chatScroll"

import { useObservabilitySessionId } from "@/hooks/useObservabilitySessionId"
import { Box, Stack } from "@open-ui-kit/core"

import ChatAreaComposer from "./ChatAreaComposer"
import ChatAreaMessageThread from "./ChatAreaMessageThread"
import ChatHeader from "./ChatHeader"

import type { GraphConfig } from "@/utils/graphConfigs"
import type { AuctionStreamingState } from "@/stores/auctionStreaming.types"
import type { RecruiterStreamingState } from "@/stores/recruiterStreaming.types"
import type { ApiResponse } from "@/types/api"
import { CanvasMode } from "@/types/patternDoc"
import { usePatternChatAPI } from "@/hooks/usePatternChatAPI"
import { streamPatternChat } from "./streamPatternChat"
import { usesStreamingChatSend } from "@/utils/patternUtils"

/** Panel expanded/collapsed by the chat header minimize control. */
export const CHAT_MESSAGE_PANEL_ID = "chat-message-panel"

interface ChatAreaProps {
  isBottomLayout: boolean
  showCoffeePrompts?: boolean
  showLogisticsPrompts?: boolean
  showDiscoveryPrompts?: boolean
  showProgressTracker?: boolean
  showAuctionStreaming?: boolean
  showRecruiterStreaming?: boolean
  showFinalResponse?: boolean
  onStreamComplete?: () => void
  onSenderHighlight?: (nodeId: string) => void
  pattern?: string
  graphConfig?: GraphConfig
  onSendPrompt?: (query: string) => void | Promise<void>
  onUserInput?: (query: string) => void
  onApiResponse?: (response: ApiResponse | string, isError?: boolean) => void
  onPatternChatSuccess?: () => void
  onClearConversation?: () => void
  currentUserMessage?: string
  agentResponse?: ApiResponse
  executionKey?: string
  isAgentLoading?: boolean
  apiError: boolean
  chatRef?: React.RefObject<HTMLDivElement | null>
  auctionState?: AuctionStreamingState
  recruiterState?: RecruiterStreamingState
  canvasMode?: CanvasMode
  selectedReferencePattern?: string | null
  patternChatSessionId?: string | null
  grafanaUrl?: string
}

const ChatArea: React.FC<ChatAreaProps> = ({
  isBottomLayout,
  showCoffeePrompts = false,
  showLogisticsPrompts = false,
  showDiscoveryPrompts = false,
  showProgressTracker = false,
  showAuctionStreaming = false,
  showRecruiterStreaming = false,
  showFinalResponse = false,
  onStreamComplete,
  onSenderHighlight,
  pattern,
  graphConfig,
  onSendPrompt,
  onUserInput,
  onApiResponse,
  onPatternChatSuccess,
  onClearConversation,
  currentUserMessage,
  agentResponse,
  executionKey,
  isAgentLoading,
  apiError,
  chatRef,
  auctionState,
  recruiterState,
  canvasMode,
  selectedReferencePattern,
  patternChatSessionId,
  grafanaUrl = getGrafanaUrl(),
}) => {
  const [content, setContent] = useState<string>("")
  const [loading, setLoading] = useState<boolean>(false)
  const [isMinimized, setIsMinimized] = useState<boolean>(false)
  const messagePanelRef = useRef<HTMLDivElement>(null)
  const threadContentRef = useRef<HTMLDivElement>(null)
  const { sendPatternMessage } = usePatternChatAPI()

  useScrollPanelOnContentResize(
    messagePanelRef,
    threadContentRef,
    Boolean(currentUserMessage) && !isMinimized,
  )

  const handleMinimize = () => {
    setIsMinimized(true)
  }

  const handleRestore = () => {
    setIsMinimized(false)
  }

  const handleSuggestedPromptSelect = (query: string) => {
    if (isMinimized) {
      setIsMinimized(false)
    }
    setContent(query)
  }

  const processMessageWithQuery = async (
    messageContent: string,
  ): Promise<void> => {
    if (!messageContent.trim()) return

    setContent("")
    setLoading(true)
    setButtonClicked(true)

    await sendMessageWithCallback(
      messageContent,
      setMessages,
      {
        onSuccess: (response: ApiResponse) => {
          setAiReplied(true)

          logger.debug("[ChatArea] API call successful, response:", response)

          if (onApiResponse) {
            onApiResponse(response.response ?? "", false)
          }
        },
        onError: (error) => {
          logger.apiError(LUNGO_FRONTEND_URLS.apiPaths.agentPrompt, error)
          const { message: errorMessage } = parseApiError(error)
          if (onApiResponse) {
            onApiResponse(errorMessage, true)
          }
        },
      },
      pattern,
    )

    setLoading(false)
  }
  const processMessage = async (): Promise<void> => {
    if (isMinimized) {
      setIsMinimized(false)
    }

    if (
      canvasMode === CanvasMode.PATTERN_DOC &&
      selectedReferencePattern &&
      patternChatSessionId
    ) {
      const msg = content
      setContent("")
      await streamPatternChat({
        patternName: selectedReferencePattern,
        sessionId: patternChatSessionId,
        message: msg,
        send: sendPatternMessage,
        onUserInput,
        onApiResponse,
        onStart: () => setLoading(true),
        onSettled: () => setLoading(false),
        onSuccess: () => onPatternChatSuccess?.(),
      })
      return
    }

    if (!content.trim() || !onSendPrompt) {
      return
    }

    const msg = content
    setContent("")
    setLoading(true)
    try {
      await onSendPrompt(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      void processMessage()
    }
  }

  const observabilitySessionId = useObservabilitySessionId(
    agentResponse?.session_id,
    agentResponse?.trace_id,
  )

  if (!isBottomLayout) {
    return null
  }

  const chatHorizontalPadding = { xs: 2, sm: 4, md: 8, lg: 15 }

  return (
    <Box
      ref={chatRef}
      sx={{
        position: "relative",
        display: "flex",
        width: "100%",
        height: "100%",
        maxHeight: "100%",
        minHeight: 0,
        flexDirection: "column",
        boxSizing: "border-box",
        overflow: "hidden",
        borderTop: "1px solid",
        borderColor: "divider",
        backgroundColor: (theme) => theme.palette.action.selected,
      }}
    >
      {currentUserMessage ? (
        <Box sx={{ flexShrink: 0, width: "100%" }}>
          <ChatHeader
            onMinimize={isMinimized ? handleRestore : handleMinimize}
            onClearConversation={onClearConversation}
            isMinimized={isMinimized}
            messagePanelId={CHAT_MESSAGE_PANEL_ID}
            horizontalPadding={chatHorizontalPadding}
          />
        </Box>
      ) : null}

      <Box
        ref={messagePanelRef}
        id={CHAT_MESSAGE_PANEL_ID}
        role="region"
        aria-label="Chat messages"
        aria-hidden={isMinimized ? true : undefined}
        sx={{
          flex: "1 1 auto",
          minHeight: 0,
          width: "100%",
          overflowY: "auto",
          overflowX: "hidden",
          // Reserve the scrollbar gutter on both edges so the centered thread
          // doesn't shift left when a scrollbar appears (keeps it aligned with
          // the composer below).
          scrollbarGutter: "stable both-edges",
          ...(currentUserMessage
            ? { borderTop: "1px solid", borderColor: "divider" }
            : { display: "none" }),
        }}
      >
        <Stack
          ref={threadContentRef}
          alignItems="center"
          spacing={1}
          sx={{
            width: "100%",
            px: chatHorizontalPadding,
            py: currentUserMessage ? 1 : 0,
            display: isMinimized ? "none" : "flex",
          }}
        >
          {currentUserMessage ? (
            <ChatAreaMessageThread
              currentUserMessage={currentUserMessage}
              isMinimized={isMinimized}
              showProgressTracker={showProgressTracker}
              showAuctionStreaming={showAuctionStreaming}
              showRecruiterStreaming={showRecruiterStreaming}
              showFinalResponse={showFinalResponse}
              isAgentLoading={!!isAgentLoading}
              agentResponse={agentResponse}
              apiError={apiError}
              graphConfig={graphConfig}
              executionKey={executionKey}
              auctionState={auctionState}
              recruiterState={recruiterState}
              observabilitySessionId={observabilitySessionId}
              onStreamComplete={onStreamComplete}
              onSenderHighlight={onSenderHighlight}
            />
          ) : null}
        </Stack>
      </Box>

      <Stack
        alignItems="space-between"
        spacing={1}
        sx={{
          flexShrink: 0,
          width: "100%",
          px: chatHorizontalPadding,
          py: currentUserMessage ? 1 : 2,
          borderTop: currentUserMessage ? "1px solid" : "none",
          borderColor: "divider",
        }}
      >
        <ChatAreaComposer
          showCoffeePrompts={showCoffeePrompts}
          showLogisticsPrompts={showLogisticsPrompts}
          showDiscoveryPrompts={showDiscoveryPrompts}
          pattern={pattern}
          onSuggestedPromptSelect={handleSuggestedPromptSelect}
          content={content}
          setContent={setContent}
          loading={loading}
          onSend={() => void processMessage()}
          onKeyDown={handleKeyDown}
        />
      </Stack>
    </Box>
  )
}

export default ChatArea
