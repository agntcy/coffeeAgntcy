/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback, useRef, useState } from "react"

import { useScrollPanelOnContentResize } from "@/utils/chatScroll"

import type { Message } from "./types"
import { parseApiError } from "@/utils/const"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import { useGroupSessionId } from "@/stores/groupStreamingStore"
import { Box, Stack } from "@open-ui-kit/core"

import ChatAreaComposer from "./ChatAreaComposer"
import ChatAreaMessageThread from "./ChatAreaMessageThread"
import ChatHeader from "./ChatHeader"
import { getChatAreaBackgroundColor } from "./chatAreaBackground"

import { logger } from "@/utils/logger"
import {
  buildGrafanaSessionDashboardUrl,
  getGrafanaUrl,
  LUNGO_FRONTEND_URLS,
} from "@/urls"
import type { GraphConfig } from "@/utils/graphConfigs"
import { DiscoveryResponseEvent } from "@/types/agent"
import type { AuctionStreamingState } from "@/stores/auctionStreaming.types"
import type { RecruiterStreamingState } from "@/stores/recruiterStreaming.types"
import type { ApiResponse } from "@/types/api"
import { PATTERNS } from "@/utils/patternUtils"

/** Panel expanded/collapsed by the chat header minimize control. */
export const CHAT_MESSAGE_PANEL_ID = "chat-message-panel"

interface ChatAreaProps {
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  setButtonClicked: (clicked: boolean) => void
  setAiReplied: (replied: boolean) => void
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
  onSendPrompt?: (query: string) => void
  onUserInput?: (query: string) => void
  onApiResponse?: (response: string, isError?: boolean) => void
  onClearConversation?: () => void
  currentUserMessage?: string
  agentResponse?: ApiResponse
  executionKey?: string
  isAgentLoading?: boolean
  apiError: boolean
  chatRef?: React.RefObject<HTMLDivElement | null>
  auctionState?: AuctionStreamingState
  recruiterState?: RecruiterStreamingState
  grafanaUrl?: string
  onDiscoveryResponse?: (evt: DiscoveryResponseEvent) => void
}

const ChatArea: React.FC<ChatAreaProps> = ({
  setMessages,
  setButtonClicked,
  setAiReplied,
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
  onClearConversation,
  currentUserMessage,
  agentResponse,
  executionKey,
  isAgentLoading,
  apiError,
  chatRef,
  auctionState,
  recruiterState,
  grafanaUrl = getGrafanaUrl(),
  onDiscoveryResponse,
}) => {
  const [content, setContent] = useState<string>("")
  const [loading, setLoading] = useState<boolean>(false)
  const [isMinimized, setIsMinimized] = useState<boolean>(false)
  const messagePanelRef = useRef<HTMLDivElement>(null)
  const threadContentRef = useRef<HTMLDivElement>(null)
  const { sendMessageWithCallback } = useAgentAPI()

  useScrollPanelOnContentResize(
    messagePanelRef,
    threadContentRef,
    Boolean(currentUserMessage) && !isMinimized,
  )

  const onApiSuccess = useCallback(
    (apiResponse: ApiResponse) => {
      if (pattern !== PATTERNS.A2A_HTTP) {
        return
      }

      onDiscoveryResponse?.({
        response: apiResponse.response,
        ts: Date.now(),
        sessionId: apiResponse.session_id,
        agent_records: apiResponse.agent_records,
      })
    },
    [pattern, onDiscoveryResponse],
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

          onApiSuccess(response)

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

    if (onUserInput) {
      onUserInput(content)
    }

    if (
      (showAuctionStreaming || showProgressTracker || showRecruiterStreaming) &&
      onSendPrompt
    ) {
      setContent("")
      onSendPrompt(content)
    } else {
      await processMessageWithQuery(content)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      processMessage()
    }
  }

  const groupSessionId = useGroupSessionId()
  const sessionIdForUrl = agentResponse?.session_id || groupSessionId

  const grafanaSessionUrl = sessionIdForUrl
    ? buildGrafanaSessionDashboardUrl(sessionIdForUrl)
    : grafanaUrl

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
        backgroundColor: (theme) => getChatAreaBackgroundColor(theme),
      }}
    >
      {currentUserMessage ? (
        <Box sx={{ flexShrink: 0, width: "100%" }}>
          <ChatHeader
            onMinimize={isMinimized ? handleRestore : handleMinimize}
            onClearConversation={onClearConversation}
            isMinimized={isMinimized}
            messagePanelId={CHAT_MESSAGE_PANEL_ID}
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
            display: isMinimized ? "none" : "block",
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
              pattern={pattern}
              graphConfig={graphConfig}
              executionKey={executionKey}
              auctionState={auctionState}
              recruiterState={recruiterState}
              groupSessionId={groupSessionId}
              grafanaSessionUrl={grafanaSessionUrl}
              onStreamComplete={onStreamComplete}
              onSenderHighlight={onSenderHighlight}
            />
          ) : null}
        </Stack>
      </Box>

      <Stack
        alignItems="center"
        spacing={1}
        sx={{
          flexShrink: 0,
          width: "100%",
          px: chatHorizontalPadding,
          py: currentUserMessage ? 1 : 2,
          borderTop: currentUserMessage ? "1px solid" : "none",
          borderColor: "divider",
          bgcolor: (theme) => getChatAreaBackgroundColor(theme),
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
          onSend={processMessage}
          onKeyDown={handleKeyDown}
        />
      </Stack>
    </Box>
  )
}

export default ChatArea
