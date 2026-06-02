/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback, useState } from "react"

import type { Message } from "./types"
import { parseApiError } from "@/utils/const"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import { useGroupSessionId } from "@/stores/groupStreamingStore"
import { Box, Stack } from "@open-ui-kit/core"

import ChatAreaComposer from "./ChatAreaComposer"
import ChatAreaMessageThread from "./ChatAreaMessageThread"
import ChatHeader from "./ChatHeader"

import { env } from "@/utils/env"
import { logger } from "@/utils/logger"
import type { GraphConfig } from "@/utils/graphConfigs"
import { DiscoveryResponseEvent } from "@/types/agent"
import type { AuctionStreamingState } from "@/stores/auctionStreaming.types"
import type { RecruiterStreamingState } from "@/stores/recruiterStreaming.types"
import type { ApiResponse } from "@/types/api"
import { PATTERNS } from "@/utils/patternUtils"

const DEFAULT_GRAFANA_URL = "http://127.0.0.1:3001"
const GRAFANA_URL = env.get("VITE_GRAFANA_URL") || DEFAULT_GRAFANA_URL
const GRAFANA_DASHBOARD_PATH =
  "/d/lungo-dashboard/lungo-dashboard?orgId=1&var-session_id="

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
  onDropdownSelect?: (query: string) => void
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
  onDropdownSelect,
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
  grafanaUrl = GRAFANA_URL,
  onDiscoveryResponse,
}) => {
  const [content, setContent] = useState<string>("")
  const [loading, setLoading] = useState<boolean>(false)
  const [isMinimized, setIsMinimized] = useState<boolean>(false)
  const { sendMessageWithCallback } = useAgentAPI()

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
          logger.apiError("/agent/prompt", error)
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
      onDropdownSelect
    ) {
      setContent("")
      onDropdownSelect(content)
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
    ? `${grafanaUrl}${GRAFANA_DASHBOARD_PATH}${encodeURIComponent(sessionIdForUrl)}`
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
      }}
    >
      {currentUserMessage ? (
        <Box sx={{ flexShrink: 0, width: "100%" }}>
          <ChatHeader
            onMinimize={isMinimized ? handleRestore : handleMinimize}
            onClearConversation={onClearConversation}
            isMinimized={isMinimized}
          />
        </Box>
      ) : null}

      <Box
        sx={{
          flex: "1 1 auto",
          minHeight: 0,
          width: "100%",
          overflowY: "auto",
          overflowX: "hidden",
          ...(currentUserMessage
            ? { borderTop: "1px solid", borderColor: "divider" }
            : {}),
        }}
      >
        <Stack
          alignItems="center"
          spacing={1}
          sx={{
            width: "100%",
            minHeight: currentUserMessage ? 0 : 120,
            px: chatHorizontalPadding,
            py: currentUserMessage ? 1 : 0,
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
          bgcolor: "background.paper",
        }}
      >
        <ChatAreaComposer
          showCoffeePrompts={showCoffeePrompts}
          showLogisticsPrompts={showLogisticsPrompts}
          showDiscoveryPrompts={showDiscoveryPrompts}
          pattern={pattern}
          onDropdownSelect={handleDropdownQuery}
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
