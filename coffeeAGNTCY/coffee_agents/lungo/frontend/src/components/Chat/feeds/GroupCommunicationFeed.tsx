/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback, useRef } from "react"
import { Box, Stack, Typography } from "@open-ui-kit/core"
import CheckCircleIcon from "@mui/icons-material/CheckCircle"

import { ChatAgentAvatar } from "../ChatAvatarCircle"
import {
  buildSenderToNodeMap,
  formatAgentName,
  getAllAgentNodeIds,
} from "../groupCommunicationFeedMapping"
import type { GraphConfig } from "@/utils/graphConfigs"
import type { LogisticsStreamStep } from "@/stores/groupStreaming.types"
import {
  useGroupEvents,
  useGroupError,
  useGroupCurrentOrderId,
  useGroupIsComplete,
} from "@/stores/groupStreamingStore"
import { FeedSpinnerRow } from "../FeedSpinnerRow"
import { FeedStatusLine } from "../FeedStatusLine"
import { FeedCollapseButton } from "./FeedCollapseButton"

export interface GroupCommunicationFeedProps {
  isVisible: boolean
  onComplete?: () => void
  prompt: string
  onStreamComplete?: () => void
  onSenderHighlight?: (nodeId: string) => void
  graphConfig?: GraphConfig
  executionKey?: string
  apiError: boolean
}

const GroupCommunicationFeed: React.FC<GroupCommunicationFeedProps> = ({
  isVisible,
  onComplete,
  prompt,
  onSenderHighlight,
  graphConfig,
  executionKey,
  apiError,
}) => {
  const groupEvents = useGroupEvents()
  const groupError = useGroupError()
  const groupCurrentOrderId = useGroupCurrentOrderId()
  const storeIsComplete = useGroupIsComplete()

  const [isExpanded, setIsExpanded] = useState(true)

  const lastProcessedEventRef = useRef<string | null>(null)
  const highlightTimeoutsRef = useRef<number[]>([])

  const toggleDetailsExpanded = useCallback(() => {
    setIsExpanded((v) => !v)
  }, [])

  useEffect(() => {
    if (prompt) {
      highlightTimeoutsRef.current.forEach(clearTimeout)
      highlightTimeoutsRef.current = []

      setIsExpanded(true)
      lastProcessedEventRef.current = null
    }
  }, [prompt])

  useEffect(() => {
    if (executionKey) {
      highlightTimeoutsRef.current.forEach(clearTimeout)
      highlightTimeoutsRef.current = []

      setIsExpanded(true)
      lastProcessedEventRef.current = null
    }
  }, [executionKey])

  useEffect(() => {
    return () => {
      highlightTimeoutsRef.current.forEach(clearTimeout)
    }
  }, [])

  useEffect(() => {
    if (!groupEvents.length) return

    const lastEvent = groupEvents[groupEvents.length - 1]
    const eventKey = `${lastEvent.order_id}-${lastEvent.timestamp}-${lastEvent.sender}-${lastEvent.receiver}`

    if (lastProcessedEventRef.current === eventKey) {
      return
    }

    lastProcessedEventRef.current = eventKey

    if (onSenderHighlight && lastEvent.sender && graphConfig) {
      const senderToNodeMap = buildSenderToNodeMap(graphConfig)
      const senderNodeId =
        senderToNodeMap[lastEvent.sender] ||
        senderToNodeMap[lastEvent.sender.toLowerCase()]

      if (senderNodeId) {
        onSenderHighlight(senderNodeId)

        if (lastEvent.sender === "Supervisor") {
          highlightTimeoutsRef.current.forEach(clearTimeout)
          highlightTimeoutsRef.current = []

          const allAgentIds = getAllAgentNodeIds(graphConfig)

          const highlightAgents = (nodeIds: string[], startIndex = 0) => {
            if (startIndex >= nodeIds.length) return

            const timeoutId = window.setTimeout(() => {
              onSenderHighlight(nodeIds[startIndex])
              highlightAgents(nodeIds, startIndex + 1)
            }, 100)

            highlightTimeoutsRef.current.push(timeoutId)
          }

          highlightAgents(allAgentIds)
        }
      }
    }

    const isFinalStep = lastEvent.state === "DELIVERED"

    if (isFinalStep && onComplete) {
      onComplete()
    }
  }, [groupEvents, onSenderHighlight, graphConfig, onComplete])

  if (!isVisible) {
    return null
  }

  const events = groupEvents || []
  const errorMessage = groupError || null

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
        ) : storeIsComplete && groupCurrentOrderId ? (
          <FeedStatusLine>Order {groupCurrentOrderId}</FeedStatusLine>
        ) : prompt && !apiError ? (
          <FeedStatusLine showDots>Processing Request</FeedStatusLine>
        ) : null}

        {prompt && !storeIsComplete && !apiError && events.length === 0 ? (
          <FeedSpinnerRow mt={3} />
        ) : null}

        {isExpanded && (
          <Stack
            spacing={3}
            sx={{ mt: 3, width: "100%", alignItems: "flex-start" }}
          >
            {events.map((step: LogisticsStreamStep, index: number) => {
              return (
                <Stack
                  key={`${step.order_id}-${index}`}
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
                      <Typography component="span">
                        {formatAgentName(step.sender)}
                      </Typography>
                      {index === 0 && (
                        <>
                          {" "}
                          → <Typography component="span">All Agents</Typography>
                        </>
                      )}
                      :{" "}
                      <Typography component="span">
                        &quot;{step.message}&quot;
                      </Typography>
                    </Typography>
                  </Box>
                </Stack>
              )
            })}

            {events.length > 0 && !storeIsComplete ? (
              <FeedSpinnerRow mt={0} />
            ) : null}
          </Stack>
        )}

        {storeIsComplete && (
          <FeedCollapseButton
            expanded={isExpanded}
            onToggle={toggleDetailsExpanded}
            expandLabel="View Details"
            collapseLabel="Collapse details"
          />
        )}
      </Stack>
    </Stack>
  )
}

export default GroupCommunicationFeed
