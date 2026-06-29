/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Scrollable chat messages, feeds, and agent responses (between header and composer).
 */

import React from "react"
import { Box, Stack, Typography } from "@open-ui-kit/core"
import { ChatAgentAvatar } from "./ChatAvatarCircle"
import { LoadingDots } from "@/components/loading"
import Message from "./Message"
import ChatMarkdown from "./ChatMarkdown"
import UserMessage from "./UserMessage"
import {
  GroupCommunicationFeed,
  AuctionStreamingFeed,
  RecruiterStreamingFeed,
} from "./feeds"
import type { GraphConfig } from "@/utils/graphConfigs"
import type { AuctionStreamingState } from "@/stores/auctionStreaming.types"
import type { RecruiterStreamingState } from "@/stores/recruiterStreaming.types"
import type { ApiResponse } from "@/types/api"
import { visuallyHiddenSx } from "@/utils/a11ySx"
import GrafanaSessionLink from "./GrafanaSessionLink"

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
  graphConfig?: GraphConfig
  executionKey?: string
  auctionState?: AuctionStreamingState
  recruiterState?: RecruiterStreamingState
  observabilitySessionId: string | null
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
  graphConfig,
  executionKey,
  auctionState,
  recruiterState,
  observabilitySessionId,
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
          observabilitySessionId={observabilitySessionId}
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
          observabilitySessionId={observabilitySessionId}
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
            {!isAgentLoading && (
              <GrafanaSessionLink sessionId={observabilitySessionId} />
            )}
          </>
        )}
      </Message>
    )}
  </Stack>
)

export default ChatAreaMessageThread
