/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback, useRef } from "react"
import CheckCircleIcon from "@mui/icons-material/CheckCircle"
import { Box, Stack, Typography } from "@open-ui-kit/core"
import { ChatAgentAvatar } from "../ChatAvatarCircle"
import { FeedSpinnerRow } from "../FeedSpinnerRow"
import { FeedStatusLine } from "../FeedStatusLine"
import { FeedErrorMessage } from "./FeedErrorMessage"
import { FeedCollapseButton } from "./FeedCollapseButton"
import GrafanaSessionLink from "../GrafanaSessionLink"
import type {
  RecruiterStreamingFeedProps,
  RecruiterStreamingEvent,
} from "@/stores/recruiterStreaming.types"
import { NDJSON_STREAMING_STATUS } from "@/stores/ndjsonStreamingStatus"
import { RECRUITER_STREAM_EVENT_TYPE } from "@/stores/recruiterStreamEventType"
import { resolveStreamAuthorToNodeId } from "../chatStreamGraphHighlight"

const RecruiterStreamingFeed: React.FC<RecruiterStreamingFeedProps> = ({
  isVisible,
  onComplete,
  prompt,
  onStreamComplete,
  onSenderHighlight,
  graphConfig,
  recruiterStreamingState,
  apiError,
  observabilitySessionId,
}) => {
  const isComplete =
    recruiterStreamingState?.status === NDJSON_STREAMING_STATUS.COMPLETED
  const [isExpanded, setIsExpanded] = useState(true)
  const hasAutoCollapsedRef = useRef(false)
  const lastProcessedEventRef = useRef<string | null>(null)

  const toggleDetailsExpanded = useCallback(() => {
    setIsExpanded((v) => !v)
  }, [])

  // Auto-expand when a new prompt arrives and reset auto-collapse flag
  useEffect(() => {
    if (prompt) {
      setIsExpanded(true)
      hasAutoCollapsedRef.current = false
      lastProcessedEventRef.current = null
    }
  }, [prompt])

  useEffect(() => {
    const events = recruiterStreamingState?.events ?? []
    if (!events.length || !onSenderHighlight) return

    const lastEvent = events[events.length - 1]
    if (lastEvent.event_type !== RECRUITER_STREAM_EVENT_TYPE.STATUS_UPDATE)
      return

    const eventKey = `${lastEvent.event_type}-${lastEvent.author ?? ""}-${lastEvent.message ?? ""}-${events.length}`
    if (lastProcessedEventRef.current === eventKey) return
    lastProcessedEventRef.current = eventKey

    const nodeId = resolveStreamAuthorToNodeId(lastEvent.author, graphConfig)
    if (nodeId) {
      onSenderHighlight(nodeId)
    }
  }, [recruiterStreamingState?.events, onSenderHighlight, graphConfig])

  // Auto-collapse once when streaming completes
  useEffect(() => {
    if (isComplete && recruiterStreamingState?.events.length > 0) {
      if (!hasAutoCollapsedRef.current) {
        hasAutoCollapsedRef.current = true
        setIsExpanded(false)
      }

      onComplete?.()
      onStreamComplete?.()
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
  const showsEvents = isExpanded && events.length > 0
  const showsCompleteFooter = isComplete && events.length > 1

  if (
    !showsStatusLine &&
    !showsSpinner &&
    !showsEvents &&
    !showsCompleteFooter
  ) {
    return null
  }

  const statusUpdates = events.filter(
    (e: RecruiterStreamingEvent) =>
      e.event_type === RECRUITER_STREAM_EVENT_TYPE.STATUS_UPDATE,
  )

  return (
    <Stack
      direction="row"
      alignItems="flex-start"
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
          <Stack direction="row" alignItems="center" flexWrap="wrap" gap={0.5}>
            <FeedStatusLine>{`Recruiter completed${events.length > 1 ? ":" : "."}`}</FeedStatusLine>
            <GrafanaSessionLink sessionId={observabilitySessionId} />
          </Stack>
        ) : prompt && !apiError ? (
          <Stack direction="row" alignItems="center" flexWrap="wrap" gap={0.5}>
            <FeedStatusLine showDots>Recruiting agents</FeedStatusLine>
            <GrafanaSessionLink sessionId={observabilitySessionId} />
          </Stack>
        ) : null}

        {prompt &&
        !isComplete &&
        !apiError &&
        !errorMessage &&
        events.length === 0 ? (
          <FeedSpinnerRow mt={3} />
        ) : null}

        {isExpanded && (
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
                      {event.author && (
                        <Typography component="span" variant="body1">
                          {event.author}:{" "}
                        </Typography>
                      )}
                      <Typography component="span" variant="body1">
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
        )}

        {isComplete && events.length > 1 && (
          <FeedCollapseButton
            expanded={isExpanded}
            onToggle={toggleDetailsExpanded}
            expandLabel="View Streaming Events"
            collapseLabel="Collapse events"
          />
        )}
      </Stack>
    </Stack>
  )
}

export default RecruiterStreamingFeed
