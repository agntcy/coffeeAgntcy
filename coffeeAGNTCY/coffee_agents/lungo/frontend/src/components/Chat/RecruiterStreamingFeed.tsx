/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback, useRef } from "react"
import { IconButton, Spinner } from "@open-ui-kit/core"
import ExpandMore from "@mui/icons-material/ExpandMore"
import ExpandLess from "@mui/icons-material/ExpandLess"
import Box from "@mui/material/Box"
import AgentIcon from "@/assets/Coffee_Icon.svg"
import CheckCircle from "@/assets/Check_Circle.png"
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
    <div className="flex w-full flex-row items-start gap-1 transition-all duration-300">
      <div className="chat-avatar-container flex h-10 w-10 flex-none items-center justify-center rounded-full bg-action-background">
        <Box
          component="img"
          src={AgentIcon}
          alt="Agent"
          sx={{
            width: 22,
            height: 22,
          }}
        />
      </div>

      <div className="flex max-w-[calc(100%-3rem)] flex-1 flex-col items-start rounded p-1 px-2">
        {errorMessage ? (
          <div className="whitespace-pre-wrap break-words font-cisco text-sm font-normal leading-5 text-chat-text">
            Connection error: {errorMessage}
          </div>
        ) : isComplete ? (
          <div className="whitespace-pre-wrap break-words font-cisco text-sm font-bold leading-5 text-chat-text">
            Recruiter completed:
          </div>
        ) : prompt && !apiError ? (
          <div className="whitespace-pre-wrap break-words font-cisco text-sm font-bold leading-5 text-chat-text">
            Recruiting agents<span className="loading-dots ml-1"></span>
          </div>
        ) : null}

        {prompt && !isComplete && !apiError && events.length === 0 && (
          <div className="mt-3 flex w-full flex-row items-start gap-1">
            <div className="mt-1 flex items-center">
              <Spinner size={16} thickness={4} />
            </div>
            <div className="flex-1"></div>
          </div>
        )}

        {isComplete && !isExpanded && (
          <div className="mt-1 flex w-full flex-row items-center gap-1 hover:opacity-75">
            <IconButton
              size="small"
              color="inherit"
              aria-label="View streaming events"
              onClick={handleExpand}
              sx={{ flex: "none", p: 0.25 }}
            >
              <ExpandMore sx={{ fontSize: 16 }} />
            </IconButton>
            <div className="flex-1">
              <span
                className="cursor-pointer font-cisco text-sm font-normal leading-[18px] text-chat-text"
                onClick={handleExpand}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault()
                    handleExpand()
                  }
                }}
                role="button"
                tabIndex={0}
              >
                View Streaming Events
              </span>
            </div>
          </div>
        )}

        {isExpanded && (
          <>
            <div className="mt-3 flex w-full flex-col items-start gap-3">
              {statusUpdates.map(
                (event: RecruiterStreamingEvent, index: number) => (
                  <div
                    key={`recruiter-status-${index}`}
                    className="flex w-full flex-row items-start gap-1"
                  >
                    <div className="mt-1 flex items-center">
                      <Box
                        component="img"
                        src={CheckCircle}
                        alt="Complete"
                        sx={{
                          width: 16,
                          height: 16,
                        }}
                      />
                    </div>
                    <div className="flex-1">
                      <div className="font-inter text-sm leading-[18px] text-chat-text">
                        {event.author && (
                          <span className="font-bold">{event.author}: </span>
                        )}
                        <span className="font-normal">{event.message}</span>
                      </div>
                    </div>
                  </div>
                ),
              )}

              {events.length > 0 && !isComplete && (
                <div className="flex w-full flex-row items-start gap-1">
                  <div className="mt-1 flex items-center">
                    <Spinner size={16} thickness={4} />
                  </div>
                  <div className="flex-1"></div>
                </div>
              )}
            </div>

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
                <ExpandLess sx={{ fontSize: 16 }} />
              </IconButton>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default RecruiterStreamingFeed
