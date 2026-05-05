/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback, useState } from "react"

import type { Message } from "./types"
import { parseApiError } from "@/utils/const"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import { useGroupSessionId } from "@/stores/groupStreamingStore"
import { Box, Stack, Typography } from "@open-ui-kit/core"

import grafanaIcon from "@/assets/grafana.svg"

import ChatAreaComposer from "./ChatAreaComposer"
import { ChatAgentAvatar } from "./ChatAvatarCircle"
import { LoadingDots } from "@/components/loading"
import UserMessage from "./UserMessage"
import ChatHeader from "./ChatHeader"
import ExternalLinkButton from "./ExternalLinkButton"
import {
  GroupCommunicationFeed,
  AuctionStreamingFeed,
  RecruiterStreamingFeed,
} from "./feeds"

import { env } from "@/utils/env"
import { logger } from "@/utils/logger"
import type { GraphConfig } from "@/utils/graphConfigs"
import { DiscoveryResponseEvent } from "@/types/agent"
import type { AuctionStreamingState } from "@/stores/auctionStreaming.types"
import type { RecruiterStreamingState } from "@/stores/recruiterStreaming.types"
import type { ApiResponse } from "@/types/api"

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
      if (pattern !== "on_demand_discovery") {
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

  return (
    <Box
      ref={chatRef}
      sx={{
        position: "relative",
        display: "flex",
        width: "100%",
        flexDirection: "column",
      }}
    >
      {currentUserMessage && (
        <ChatHeader
          onMinimize={isMinimized ? handleRestore : handleMinimize}
          onClearConversation={onClearConversation}
          isMinimized={isMinimized}
          showActions={!!agentResponse && !isAgentLoading}
        />
      )}

      <Stack
        alignItems="center"
        spacing={1}
        sx={{
          width: "100%",
          minHeight: currentUserMessage ? "auto" : 120,
          px: { xs: 2, sm: 4, md: 8, lg: 15 },
          py: currentUserMessage ? 1 : 2,
        }}
      >
        {currentUserMessage && (
          <Stack spacing={1.5} sx={{ width: "100%", maxWidth: 880, mb: 2 }}>
            {!isMinimized && <UserMessage content={currentUserMessage} />}

            {showProgressTracker && (
              <Box
                sx={{
                  width: "100%",
                  display: isMinimized ? "none" : "block",
                }}
              >
                <GroupCommunicationFeed
                  isVisible={!isMinimized && showProgressTracker}
                  onComplete={onStreamComplete}
                  onSenderHighlight={onSenderHighlight}
                  graphConfig={graphConfig}
                  prompt={currentUserMessage || ""}
                  executionKey={executionKey}
                  apiError={apiError}
                />
              </Box>
            )}

            {showAuctionStreaming && (
              <Box
                sx={{
                  width: "100%",
                  display: isMinimized ? "none" : "block",
                }}
              >
                <AuctionStreamingFeed
                  isVisible={!isMinimized && showAuctionStreaming}
                  prompt={currentUserMessage || ""}
                  apiError={apiError}
                  auctionStreamingState={auctionState}
                />
              </Box>
            )}

            {showRecruiterStreaming && (
              <Box
                sx={{
                  width: "100%",
                  display: isMinimized ? "none" : "block",
                }}
              >
                <RecruiterStreamingFeed
                  isVisible={!isMinimized && showRecruiterStreaming}
                  prompt={currentUserMessage || ""}
                  apiError={apiError}
                  recruiterStreamingState={recruiterState}
                  onStreamComplete={onStreamComplete}
                />
              </Box>
            )}

            {showFinalResponse &&
              (isAgentLoading || agentResponse) &&
              !isMinimized && (
                <Stack
                  direction="row"
                  alignItems="flex-start"
                  spacing={0.5}
                  sx={{ width: "100%" }}
                >
                  <ChatAgentAvatar />
                  <Stack
                    sx={{
                      maxWidth: "calc(100% - 3rem)",
                      flex: 1,
                      alignItems: "flex-start",
                      justifyContent: "center",
                      borderRadius: 1,
                      py: 0.5,
                      px: 1,
                    }}
                  >
                    {isAgentLoading ? (
                      <Box
                        sx={{
                          whiteSpace: "pre-wrap",
                          overflowWrap: "break-word",
                          wordBreak: "break-word",
                        }}
                      >
                        <LoadingDots />
                      </Box>
                    ) : (
                      <Typography
                        variant="body2"
                        component="div"
                        sx={{
                          whiteSpace: "pre-wrap",
                          overflowWrap: "break-word",
                          wordBreak: "break-word",
                        }}
                      >
                        {agentResponse?.response ?? ""}
                        {(agentResponse?.session_id || groupSessionId) &&
                          !isAgentLoading &&
                          pattern !== "on_demand_discovery" && (
                            <ExternalLinkButton
                              url={grafanaSessionUrl}
                              label="Grafana"
                              iconSrc={grafanaIcon}
                            />
                          )}
                      </Typography>
                    )}
                  </Stack>
                </Stack>
              )}
          </Stack>
        )}

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
