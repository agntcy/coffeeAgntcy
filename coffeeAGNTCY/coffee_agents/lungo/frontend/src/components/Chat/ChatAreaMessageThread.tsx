/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Scrollable chat messages, feeds, and agent responses (between header and composer).
 */

import React from "react"
import { Box, Stack, Typography } from "@open-ui-kit/core"
import grafanaIcon from "@/assets/grafana.svg"
import { ChatAgentAvatar } from "./ChatAvatarCircle"
import { LoadingDots } from "@/components/loading"
import UserMessage from "./UserMessage"
import ExternalLinkButton from "./ExternalLinkButton"
import {
  GroupCommunicationFeed,
  AuctionStreamingFeed,
  RecruiterStreamingFeed,
} from "./feeds"
import type { GraphConfig } from "@/utils/graphConfigs"
import type { AuctionStreamingState } from "@/stores/auctionStreaming.types"
import type { RecruiterStreamingState } from "@/stores/recruiterStreaming.types"
import type { ApiResponse } from "@/types/api"
import { PATTERNS } from "@/utils/patternUtils"

export interface ChatAreaMessageThreadProps {
  currentUserMessage: string
  isMinimized: boolean
  showProgressTracker: boolean
  showAuctionStreaming: boolean
  showRecruiterStreaming: boolean
  showFinalResponse: boolean
  isAgentLoading: boolean
  agentResponse?: ApiResponse
  apiError: boolean
  pattern?: string
  graphConfig?: GraphConfig
  executionKey?: string
  auctionState?: AuctionStreamingState
  recruiterState?: RecruiterStreamingState
  groupSessionId: string | null
  grafanaSessionUrl: string
  onStreamComplete?: () => void
  onSenderHighlight?: (nodeId: string) => void
}

const ChatAreaMessageThread: React.FC<ChatAreaMessageThreadProps> = ({
  currentUserMessage,
  isMinimized,
  showProgressTracker,
  showAuctionStreaming,
  showRecruiterStreaming,
  showFinalResponse,
  isAgentLoading,
  agentResponse,
  apiError,
  pattern,
  graphConfig,
  executionKey,
  auctionState,
  recruiterState,
  groupSessionId,
  grafanaSessionUrl,
  onStreamComplete,
  onSenderHighlight,
}) => (
  <Stack spacing={1.5} sx={{ width: "100%", maxWidth: 880, mb: 2 }}>
    {!isMinimized && <UserMessage content={currentUserMessage} />}

    {showProgressTracker && (
      <Box sx={{ width: "100%", display: isMinimized ? "none" : "block" }}>
        <GroupCommunicationFeed
          isVisible={!isMinimized && showProgressTracker}
          onComplete={onStreamComplete}
          onSenderHighlight={onSenderHighlight}
          graphConfig={graphConfig}
          prompt={currentUserMessage}
          executionKey={executionKey}
          apiError={apiError}
        />
      </Box>
    )}

    {showAuctionStreaming && (
      <Box sx={{ width: "100%", display: isMinimized ? "none" : "block" }}>
        <AuctionStreamingFeed
          isVisible={!isMinimized && showAuctionStreaming}
          prompt={currentUserMessage}
          apiError={apiError}
          auctionStreamingState={auctionState}
        />
      </Box>
    )}

    {showRecruiterStreaming && (
      <Box sx={{ width: "100%", display: isMinimized ? "none" : "block" }}>
        <RecruiterStreamingFeed
          isVisible={!isMinimized && showRecruiterStreaming}
          prompt={currentUserMessage}
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
                  pattern !== PATTERNS.A2A_HTTP && (
                    <ExternalLinkButton
                      component="button"
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
)

export default ChatAreaMessageThread
