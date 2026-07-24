/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useRef } from "react"
import CheckCircleIcon from "@mui/icons-material/CheckCircle"
import { Box, Stack, Typography } from "@open-ui-kit/core"

import { ChatAgentAvatar } from "../ChatAvatarCircle"
import type { AuctionStreamingState } from "@/stores/auctionStreaming.types"
import { NDJSON_STREAMING_STATUS } from "@/stores/ndjsonStreamingStatus"
import type { GraphConfig } from "@/utils/graphConfigs"
import { animationSequenceStepIds } from "../chatStreamGraphHighlight"
import { FeedSpinnerRow } from "../FeedSpinnerRow"
import { FeedStatusLine } from "../FeedStatusLine"
import { FeedErrorMessage } from "./FeedErrorMessage"
import GrafanaSessionLink from "../GrafanaSessionLink"

export interface AuctionStreamingFeedProps {
  isVisible: boolean
  onComplete?: () => void
  prompt: string
  onStreamComplete?: () => void
  onSenderHighlight?: (nodeId: string) => void
  graphConfig?: GraphConfig
  executionKey?: string
  apiError: boolean
  auctionStreamingState?: AuctionStreamingState
  observabilitySessionId?: string | null
}

const AuctionStreamingFeed: React.FC<AuctionStreamingFeedProps> = ({
  isVisible,
  onComplete,
  prompt,
  onStreamComplete,
  onSenderHighlight,
  graphConfig,
  auctionStreamingState,
  apiError,
  observabilitySessionId,
}) => {
  const isComplete =
    auctionStreamingState?.status === NDJSON_STREAMING_STATUS.COMPLETED
  const lastProcessedStepRef = useRef<number | null>(null)

  useEffect(() => {
    if (prompt) {
      lastProcessedStepRef.current = null
    }
  }, [prompt])

  useEffect(() => {
    const events = auctionStreamingState?.events ?? []
    if (!events.length || !onSenderHighlight) return

    const stepIndex = events.length - 1
    if (lastProcessedStepRef.current === stepIndex) return
    lastProcessedStepRef.current = stepIndex

    for (const graphElementId of animationSequenceStepIds(
      graphConfig,
      stepIndex,
    )) {
      onSenderHighlight(graphElementId)
    }
  }, [auctionStreamingState?.events, onSenderHighlight, graphConfig])

  useEffect(() => {
    if (isComplete && auctionStreamingState?.events.length > 0) {
      if (onComplete) {
        onComplete()
      }

      if (onStreamComplete) {
        onStreamComplete()
      }
    }
  }, [
    isComplete,
    auctionStreamingState?.events.length,
    onComplete,
    onStreamComplete,
  ])

  if (!isVisible) {
    return null
  }

  const events = auctionStreamingState?.events || []
  const errorMessage = auctionStreamingState?.error || null

  if ((!prompt && events.length === 0) || apiError) {
    return null
  }

  if (errorMessage && events.length === 0) {
    return <FeedErrorMessage>{errorMessage}</FeedErrorMessage>
  }

  const showsStatusLine = isComplete || (Boolean(prompt) && !apiError)
  const showsSpinner =
    Boolean(prompt) &&
    !isComplete &&
    !apiError &&
    !errorMessage &&
    events.length === 0
  const showsEvents = events.length > 0

  if (!showsStatusLine && !showsSpinner && !showsEvents) {
    return null
  }

  return (
    <Stack
      direction="row"
      alignItems="flex-start"
      spacing={0.5}
      sx={{ width: "100%", transition: "all 300ms" }}
    >
      <ChatAgentAvatar />
      <Stack
        sx={{
          flex: 1,
          minWidth: 0,
          maxWidth: "calc(100% - 3rem)",
          alignItems: "flex-start",
          borderRadius: 1,
          py: 0.5,
          px: 1,
        }}
      >
        {errorMessage ? (
          <FeedErrorMessage>{errorMessage}</FeedErrorMessage>
        ) : isComplete ? (
          <FeedStatusLine>Streaming output:</FeedStatusLine>
        ) : prompt && !apiError ? (
          <FeedStatusLine showDots>Streaming</FeedStatusLine>
        ) : null}

        {prompt &&
        !isComplete &&
        !apiError &&
        !errorMessage &&
        events.length === 0 ? (
          <FeedSpinnerRow mt={3} />
        ) : null}

        {events.length > 0 ? (
          <Stack
            spacing={3}
            sx={{ mt: 3, width: "100%", alignItems: "flex-start" }}
          >
            {events.map((event, index) => {
              const isLastEvent = isComplete && index === events.length - 1
              const label = isLastEvent
                ? "Final response:"
                : `Response ${index + 1}:`

              return (
                <Stack
                  key={`auction-${index}`}
                  direction="row"
                  alignItems="flex-start"
                  spacing={0.5}
                  sx={{ width: "100%" }}
                >
                  <Box sx={{ mt: 0.5, display: "flex", alignItems: "center" }}>
                    <CheckCircleIcon
                      sx={{ color: "success.main" }}
                      aria-hidden
                    />
                  </Box>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography
                      variant="body1"
                      component="div"
                      sx={{
                        overflowWrap: "break-word",
                        wordBreak: "break-word",
                      }}
                    >
                      <Typography component="span" variant="body1">
                        {label}
                      </Typography>{" "}
                      {event.response}
                    </Typography>
                  </Box>
                </Stack>
              )
            })}

            {isComplete && events.length > 0 ? (
              <GrafanaSessionLink sessionId={observabilitySessionId} />
            ) : null}

            {events.length > 0 && !isComplete ? (
              <FeedSpinnerRow mt={0} />
            ) : null}
          </Stack>
        ) : null}
      </Stack>
    </Stack>
  )
}

export default AuctionStreamingFeed
