/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback, useRef } from "react"
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react"
import AgentIcon from "@/assets/Coffee_Icon.svg"
import CheckCircle from "@/assets/Check_Circle.png"
import { RecruiterStreamingFeedProps, RecruiterStreamingEvent } from "@/types/streaming"

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
        <img src={AgentIcon} alt="Agent" className="h-[22px] w-[22px]" />
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
              <Loader2 className="h-4 w-4 animate-spin text-accent-primary" />
            </div>
            <div className="flex-1"></div>
          </div>
        )}

        {isComplete && !isExpanded && (
          <div
            className="mt-1 flex w-full cursor-pointer flex-row items-center gap-1 hover:opacity-75"
            onClick={handleExpand}
          >
            <div className="h-4 w-4 flex-none">
              <ChevronDown className="h-4 w-4 text-chat-text" />
            </div>
            <div className="flex-1">
              <span className="font-cisco text-sm font-normal leading-[18px] text-chat-text">
                View Streaming Events
              </span>
            </div>
          </div>
        )}

        {isExpanded && (
          <>
            <div className="mt-3 flex w-full flex-col items-start gap-3">
              {statusUpdates.map((event: RecruiterStreamingEvent, index: number) => (
                <div
                  key={`recruiter-status-${index}`}
                  className="flex w-full flex-row items-start gap-1"
                >
                  <div className="mt-1 flex items-center">
                    <img src={CheckCircle} alt="Complete" className="h-4 w-4" />
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
              ))}

              {events.length > 0 && !isComplete && (
                <div className="flex w-full flex-row items-start gap-1">
                  <div className="mt-1 flex items-center">
                    <Loader2 className="h-4 w-4 animate-spin text-accent-primary" />
                  </div>
                  <div className="flex-1"></div>
                </div>
              )}
            </div>

            {isComplete && (
              <div
                className="flex w-full cursor-pointer flex-row items-center gap-1 pt-2 hover:opacity-75"
                onClick={handleCollapse}
              >
                <div className="h-4 w-4 flex-none">
                  <ChevronUp className="h-4 w-4 text-chat-text" />
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default RecruiterStreamingFeed
