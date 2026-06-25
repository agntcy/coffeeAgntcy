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
import Message from "./Message"
import ChatMarkdown from "./ChatMarkdown"
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
import { visuallyHiddenSx } from "@/utils/a11ySx"

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
  <Stack
    component="section"
    aria-label="Conversation"
    aria-live="polite"
    aria-relevant="additions text"
    aria-atomic={false}
    spacing={1.5}
    sx={{ width: "100%", maxWidth: 1100, mx: "auto", mb: 2 }}
  >
    {apiError ? (
      <Box role="alert" aria-live="assertive">
        <Typography variant="body1" color="error">
          The request failed. Check the workflow or try again.
        </Typography>
      </Box>
    ) : null}

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
          onSenderHighlight={onSenderHighlight}
          graphConfig={graphConfig}
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
          onSenderHighlight={onSenderHighlight}
          graphConfig={graphConfig}
        />
      </Box>
    )}

    {showFinalResponse && (isAgentLoading || agentResponse) && !isMinimized && (
      <Message icon={<ChatAgentAvatar />}>
        {isAgentLoading ? (
          <>
            <Box component="span" sx={visuallyHiddenSx}>
              Agent is responding
            </Box>
            <LoadingDots />
          </>
        ) : (
          <>
            <ChatMarkdown content={agentResponse?.response ?? ""} />
            {(agentResponse?.session_id || groupSessionId) &&
              !isAgentLoading &&
              pattern !== PATTERNS.A2A_HTTP && (
                <ExternalLinkButton
                  component="button"
                  url={grafanaSessionUrl}
                  label="Grafana"
                  iconSrc={grafanaIcon}
                  sx={(theme) => ({
                    ml: 1,
                    "& .MuiChip-label": theme.typography.body1,
                  })}
                />
              )}
          </>
        )}
      </Message>
    )}
  </Stack>
)

export default ChatAreaMessageThread
