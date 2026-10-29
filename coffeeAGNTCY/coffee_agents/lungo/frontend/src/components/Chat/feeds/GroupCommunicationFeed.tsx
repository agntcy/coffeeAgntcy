/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback, useRef } from "react"
import { Box, Icons, Stack, Typography } from "@open-ui-kit/core"

import { ChatAgentAvatar } from "../shared"
import {
  buildSenderToNodeMap,
  formatAgentName,
  getAllAgentNodeIds,
} from "./groupCommunicationFeedMapping"
import type { GraphConfig } from "@/utils/graphConfigs"
import type { LogisticsStreamStep } from "@/stores/groupStreaming.types"
import {
  useGroupEvents,
  useGroupNegotiationEvents,
  useGroupError,
  useGroupCurrentOrderId,
  useGroupStreamingStatus,
} from "@/stores/groupStreamingStore"
import { NDJSON_STREAMING_STATUS } from "@/stores/ndjsonStreamingStatus"
import { resolveStreamAuthorToNodeId } from "../streaming/chatStreamGraphHighlight"
import {
  isVisibleSupplyChainMessage,
  supplyChainPartyLabel,
} from "@/stores/supplyChainEvents"
import { SupplyChainEventList } from "./SupplyChainEventList"
import { FeedSpinnerRow } from "./FeedSpinnerRow"
import { successIconColorSx } from "@/utils/successIconColor"
import { FeedStatusLine } from "./FeedStatusLine"
import { FeedErrorMessage } from "./FeedErrorMessage"
import { FeedCollapseButton } from "./FeedCollapseButton"
import { GrafanaSessionLink } from "../shared"

export interface GroupCommunicationFeedProps {
  isVisible: boolean
  onComplete?: () => void
  prompt: string
  onStreamComplete?: () => void
  onSenderHighlight?: (nodeId: string) => void
  graphConfig?: GraphConfig
  executionKey?: string
  apiError: boolean
  observabilitySessionId?: string | null
}

const GroupCommunicationFeed: React.FC<GroupCommunicationFeedProps> = ({
  isVisible,
  onComplete,
  prompt,
  onSenderHighlight,
  graphConfig,
  executionKey,
  apiError,
  observabilitySessionId,
}) => {
  const groupEvents = useGroupEvents()
  const negotiationEvents = useGroupNegotiationEvents()
  const isNegotiation = negotiationEvents.length > 0
  const groupError = useGroupError()
  const groupCurrentOrderId = useGroupCurrentOrderId()
  const groupStatus = useGroupStreamingStatus()
  const isComplete = groupStatus === NDJSON_STREAMING_STATUS.COMPLETED
  const isActive =
    groupStatus === NDJSON_STREAMING_STATUS.CONNECTING ||
    groupStatus === NDJSON_STREAMING_STATUS.STREAMING

  const [isExpanded, setIsExpanded] = useState(true)

  const lastProcessedEventRef = useRef<string | null>(null)
  const lastHighlightedNegotiationRef = useRef<string | null>(null)
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
      lastHighlightedNegotiationRef.current = null
    }
  }, [prompt])

  useEffect(() => {
    if (executionKey) {
      highlightTimeoutsRef.current.forEach(clearTimeout)
      highlightTimeoutsRef.current = []

      setIsExpanded(true)
      lastProcessedEventRef.current = null
      lastHighlightedNegotiationRef.current = null
    }
  }, [executionKey])

  useEffect(() => {
    return () => {
      highlightTimeoutsRef.current.forEach(clearTimeout)
    }
  }, [])

  // Supply Chain Commitment: highlight the node of the latest speaker. The
  // highlight callback and graph config are not referentially stable, and
  // highlighting updates the parent, so a key guard stops a render loop.
  useEffect(() => {
    if (!onSenderHighlight || !graphConfig) return
    for (let i = negotiationEvents.length - 1; i >= 0; i -= 1) {
      const event = negotiationEvents[i]
      if (event.type !== "message") continue
      if (!isVisibleSupplyChainMessage(event)) continue
      const eventKey = `${i}-${event.seq}-${event.from}`
      if (lastHighlightedNegotiationRef.current === eventKey) return
      lastHighlightedNegotiationRef.current = eventKey
      const nodeId = resolveStreamAuthorToNodeId(
        supplyChainPartyLabel(event.from),
        graphConfig,
      )
      if (nodeId) onSenderHighlight(nodeId)
      return
    }
  }, [negotiationEvents, onSenderHighlight, graphConfig])

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
  const hasAnyEvents = events.length > 0 || isNegotiation
  const errorMessage = groupError || null

  if ((!prompt && !hasAnyEvents) || apiError) {
    return null
  }

  if (errorMessage && !hasAnyEvents) {
    return <FeedErrorMessage>{errorMessage}</FeedErrorMessage>
  }

  const showsStatusLine =
    (isComplete && Boolean(groupCurrentOrderId)) ||
    (Boolean(prompt) && !apiError && isActive)
  const showsSpinner = Boolean(prompt) && isActive && !apiError && !hasAnyEvents
  const showsEvents = isExpanded && hasAnyEvents
  const showsCompleteFooter = isComplete

  if (
    !showsStatusLine &&
    !showsSpinner &&
    !showsEvents &&
    !showsCompleteFooter
  ) {
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
        ) : isComplete && groupCurrentOrderId ? (
          <FeedStatusLine>Order {groupCurrentOrderId}</FeedStatusLine>
        ) : prompt && !apiError && isActive ? (
          <FeedStatusLine showDots>Processing Request</FeedStatusLine>
        ) : null}

        {prompt && isActive && !apiError && !errorMessage && !hasAnyEvents ? (
          <FeedSpinnerRow mt={3} />
        ) : null}

        {isExpanded && (
          <Stack
            spacing={3}
            sx={{ mt: 3, width: "100%", alignItems: "flex-start" }}
          >
            {isNegotiation ? (
              <SupplyChainEventList events={negotiationEvents} />
            ) : null}

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
                    <Icons.CheckCircleFilled
                      sx={(theme) => successIconColorSx(theme)}
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
                        {formatAgentName(step.sender)}
                      </Typography>
                      {index === 0 && (
                        <>
                          {" "}
                          →{" "}
                          <Typography component="span" variant="body1">
                            All Agents
                          </Typography>
                        </>
                      )}
                      :{" "}
                      <Typography component="span" variant="body1">
                        &quot;{step.message}&quot;
                      </Typography>
                    </Typography>
                  </Box>
                </Stack>
              )
            })}

            {hasAnyEvents && isActive ? <FeedSpinnerRow mt={0} /> : null}
          </Stack>
        )}

        {isComplete && (
          <>
            <GrafanaSessionLink
              sessionId={observabilitySessionId}
              sx={isNegotiation && isExpanded ? { mt: 2 } : undefined}
            />
            <FeedCollapseButton
              expanded={isExpanded}
              onToggle={toggleDetailsExpanded}
              expandLabel="View Details"
              collapseLabel="Collapse details"
            />
          </>
        )}
      </Stack>
    </Stack>
  )
}

export default GroupCommunicationFeed
