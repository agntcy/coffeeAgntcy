/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback, useRef } from "react"
import ExpandMore from "@mui/icons-material/ExpandMore"
import ExpandLess from "@mui/icons-material/ExpandLess"
import CheckCircleIcon from "@mui/icons-material/CheckCircle"
import { Box, IconButton, Stack, Typography } from "@open-ui-kit/core"
import { ChatAgentAvatar } from "../ChatAvatarCircle"
import { FeedSpinnerRow } from "../FeedSpinnerRow"
import { FeedStatusLine } from "../FeedStatusLine"
import type {
  RecruiterStreamingFeedProps,
  RecruiterStreamingEvent,
} from "@/stores/recruiterStreaming.types"

const RecruiterStreamingFeed: React.FC<RecruiterStreamingFeedProps> = ({
  isVisible,
  onComplete,
  prompt,
  onStreamComplete,
  recruiterStreamingState,
  apiError,
}) => {
  const isComplete = recruiterStreamingState?.status === "completed"
  const [isExpanded, setIsExpanded] = useState(true)
  const hasAutoCollapsedRef = useRef(false)

  const handleExpand = useCallback(() => {
    setIsExpanded(true)
  }, [])

  const handleCollapse = useCallback(() => {
    setIsExpanded(false)
  }, [])

  // Auto-expand when a new prompt arrives and reset auto-collapse flag
  useEffect(() => {
    if (prompt) {
      setIsExpanded(true)
      hasAutoCollapsedRef.current = false
    }
  }, [prompt])

  // Auto-collapse once when streaming completes
  useEffect(() => {
    if (isComplete && recruiterStreamingState?.events.length > 0) {
      if (!hasAutoCollapsedRef.current) {
        hasAutoCollapsedRef.current = true
        setIsExpanded(false)
      }

      if (onComplete) {
        onComplete()
      }

      if (onStreamComplete) {
        onStreamComplete()
      }
    }
  }, [
    isComplete,
    recruiterStreamingState?.events.length,
    onComplete,
    onStreamComplete,
  ])

  if (!isVisible) {
    return null
  }

  const events = recruiterStreamingState?.events || []
  const errorMessage = recruiterStreamingState?.error || null

  if ((!prompt && events.length === 0) || apiError) {
    return null
  }

  const statusUpdates = events.filter(
    (e: RecruiterStreamingEvent) => e.event_type === "status_update",
  )

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
          <FeedStatusLine>Recruiter completed:</FeedStatusLine>
        ) : prompt && !apiError ? (
          <FeedStatusLine showDots>Recruiting agents</FeedStatusLine>
        ) : null}

        {prompt && !isComplete && !apiError && events.length === 0 ? (
          <FeedSpinnerRow mt={3} />
        ) : null}

        {isComplete && !isExpanded && (
          <Box
            onClick={handleExpand}
            sx={{
              mt: 1,
              display: "flex",
              width: "100%",
              cursor: "pointer",
              flexDirection: "row",
              alignItems: "center",
              gap: 0.5,
              "&:hover": { opacity: 0.75 },
            }}
          >
            <IconButton
              size="small"
              color="inherit"
              aria-label="View streaming events"
              sx={{ flex: "none", p: 0.25 }}
            >
              <ExpandMore />
            </IconButton>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="body2" component="span">
                View Streaming Events
              </Typography>
            </Box>
          </Box>
        )}

        {isExpanded && (
          <>
            <Stack
              spacing={3}
              sx={{ mt: 3, width: "100%", alignItems: "flex-start" }}
            >
              {statusUpdates.map(
                (event: RecruiterStreamingEvent, index: number) => (
                  <Stack
                    key={`recruiter-status-${index}`}
                    direction="row"
                    alignItems="flex-start"
                    spacing={0.5}
                    sx={{ width: "100%" }}
                  >
                    <Box
                      sx={{ mt: 0.5, display: "flex", alignItems: "center" }}
                    >
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
                        {event.author && (
                          <Typography component="span" variant="body2">
                            {event.author}:{" "}
                          </Typography>
                        )}
                        <Typography component="span" variant="body2">
                          {event.message}
                        </Typography>
                      </Typography>
                    </Box>
                  </Stack>
                ),
              )}

              {events.length > 0 && !isComplete ? (
                <FeedSpinnerRow mt={0} />
              ) : null}
            </Stack>

            {isComplete && (
              <IconButton
                size="small"
                color="inherit"
                aria-label="Collapse streaming events"
                onClick={handleCollapse}
                sx={{
                  alignSelf: "flex-start",
                  mt: 1,
                  p: 0.25,
                }}
              >
                <ExpandLess aria-hidden />
              </IconButton>
            )}
          </>
        )}
      </Stack>
    </Stack>
  )
}

export default RecruiterStreamingFeed
