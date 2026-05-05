/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect } from "react"
import CheckCircleIcon from "@mui/icons-material/CheckCircle"
import { Box, Stack, Typography } from "@open-ui-kit/core"

import { ChatAgentAvatar } from "../ChatAvatarCircle"
import type { AuctionStreamingState } from "@/stores/auctionStreaming.types"
import { FeedSpinnerRow } from "../FeedSpinnerRow"
import { FeedStatusLine } from "../FeedStatusLine"

export interface AuctionStreamingFeedProps {
  isVisible: boolean
  onComplete?: () => void
  prompt: string
  onStreamComplete?: () => void
  executionKey?: string
  apiError: boolean
  auctionStreamingState?: AuctionStreamingState
}

const AuctionStreamingFeed: React.FC<AuctionStreamingFeedProps> = ({
  isVisible,
  onComplete,
  prompt,
  onStreamComplete,
  auctionStreamingState,
  apiError,
}) => {
  const isComplete = auctionStreamingState?.status === "completed"

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
          <FeedStatusLine>Connection error: {errorMessage}</FeedStatusLine>
        ) : isComplete ? (
          <FeedStatusLine>Streaming output:</FeedStatusLine>
        ) : prompt && !apiError ? (
          <FeedStatusLine showDots>Streaming</FeedStatusLine>
        ) : null}

        {prompt && !isComplete && !apiError && events.length === 0 ? (
          <FeedSpinnerRow mt={3} />
        ) : null}

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
                    sx={{ fontSize: 22, color: "success.main" }}
                    aria-hidden
                  />
                </Box>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography
                    variant="body2"
                    component="div"
                    sx={{
                      overflowWrap: "break-word",
                      wordBreak: "break-word",
                    }}
                  >
                    <Typography component="span" variant="body2">
                      {label}
                    </Typography>{" "}
                    {event.response}
                  </Typography>
                </Box>
              </Stack>
            )
          })}

          {events.length > 0 && !isComplete ? <FeedSpinnerRow mt={0} /> : null}
        </Stack>
      </Stack>
    </Stack>
  )
}

export default AuctionStreamingFeed
